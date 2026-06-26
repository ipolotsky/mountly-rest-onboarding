import asyncio
import hashlib
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import NamedTuple, TypeVar

from sqlalchemy.orm import Session

from app import analytics, storage
from app.config import settings
from app.database import SessionLocal
from app.graph import OnboardingState, run_pipeline
from app.ingest import IngestedFile, ingest_file
from app.models import Onboarding as OnboardingRow
from app.models import StoredFile
from app.schemas import (
    AdminMetrics,
    AdminOnboardingRow,
    BankingBlock,
    Confirmed,
    LegalBlock,
    MenuBlock,
    Onboarding,
    SourceFile,
)
from app.validators import (
    holder_matches_legal_name,
    validate_bic,
    validate_iban,
    validate_siren,
    validate_siret,
)

PRESERVED_PROVENANCE = ("user_edited", "user_added", "user_confirmed")

_BlockT = TypeVar("_BlockT")


class StoreResult(NamedTuple):
    ingested: list[IngestedFile]
    skipped_duplicates: list[str]


class UploadFile:
    filename: str
    media_type: str
    content: bytes

    def __init__(self, filename: str, media_type: str, content: bytes) -> None:
        self.filename = filename
        self.media_type = media_type
        self.content = content


class OnboardingNotFoundError(Exception):
    pass


class OnboardingService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, locale: str | None, device: str | None) -> str:
        onboarding_id = uuid.uuid4().hex[:16]
        row = OnboardingRow(
            id=onboarding_id,
            locale=locale or "fr",
            device=device or "desktop",
            step=1,
            confirmed=Confirmed().model_dump(),
            legal=LegalBlock().model_dump(),
            banking=BankingBlock().model_dump(),
            menu=MenuBlock().model_dump(),
        )
        self._session.add(row)
        self._session.flush()
        analytics.track(
            self._session,
            kind="onboarding_started",
            onboarding_id=onboarding_id,
            device=row.device,
            locale=row.locale,
        )
        self._session.commit()
        return onboarding_id

    def get(self, onboarding_id: str) -> Onboarding:
        return self._to_schema(self._require(onboarding_id))

    async def parse_legal(self, onboarding_id: str, files: list[UploadFile]) -> LegalBlock:
        row = self._require(onboarding_id)
        ingested = self._store_and_ingest(onboarding_id, files).ingested
        existing = LegalBlock.model_validate(row.legal or {})
        self._mark_block_parsing(row, "legal", existing.model_dump())

        async def work(service: "OnboardingService") -> LegalBlock:
            return await service._run_legal_parse(onboarding_id, ingested, existing)

        return await _run_detached(onboarding_id, "legal", work)

    async def parse_banking(self, onboarding_id: str, files: list[UploadFile]) -> BankingBlock:
        row = self._require(onboarding_id)
        ingested = self._store_and_ingest(onboarding_id, files).ingested
        existing = BankingBlock.model_validate(row.banking or {})
        existing_legal = LegalBlock.model_validate(row.legal or {})
        self._mark_block_parsing(row, "banking", existing.model_dump())

        async def work(service: "OnboardingService") -> BankingBlock:
            return await service._run_banking_parse(
                onboarding_id, ingested, existing, existing_legal
            )

        return await _run_detached(onboarding_id, "banking", work)

    async def parse_menu(self, onboarding_id: str, files: list[UploadFile]) -> MenuBlock:
        row = self._require(onboarding_id)
        existing = MenuBlock.model_validate(row.menu or {})
        active_file_ids = [source.id for source in existing.source_files]
        store = self._store_and_ingest(
            onboarding_id, files, dedupe=True, active_file_ids=active_file_ids
        )
        self._mark_block_parsing(row, "menu", existing.model_dump())

        async def work(service: "OnboardingService") -> MenuBlock:
            return await service._run_menu_parse(
                onboarding_id, store.ingested, existing, store.skipped_duplicates
            )

        return await _run_detached(onboarding_id, "menu", work)

    async def _run_legal_parse(
        self, onboarding_id: str, ingested: list[IngestedFile], existing: LegalBlock
    ) -> LegalBlock:
        row = self._require(onboarding_id)
        state = await run_pipeline(
            OnboardingState(document_type="legal", files=ingested, existing_legal=existing)
        )
        block = state.get("legal") or LegalBlock(status="couldnt_parse")
        block = _preserve_legal(existing, block)
        row.legal = block.model_dump()
        self._emit_parse_events(onboarding_id, row, "legal", state)
        self._session.add(row)
        self._session.commit()
        return block

    async def _run_banking_parse(
        self,
        onboarding_id: str,
        ingested: list[IngestedFile],
        existing: BankingBlock,
        existing_legal: LegalBlock,
    ) -> BankingBlock:
        row = self._require(onboarding_id)
        state = await run_pipeline(
            OnboardingState(
                document_type="banking",
                files=ingested,
                existing_banking=existing,
                existing_legal=existing_legal,
            )
        )
        block = state.get("banking") or BankingBlock(status="couldnt_parse")
        block = _preserve_banking(existing, block)
        row.banking = block.model_dump()
        self._emit_parse_events(onboarding_id, row, "banking", state)
        self._session.add(row)
        self._session.commit()
        return block

    async def _run_menu_parse(
        self,
        onboarding_id: str,
        ingested: list[IngestedFile],
        existing: MenuBlock,
        skipped_duplicates: list[str],
    ) -> MenuBlock:
        row = self._require(onboarding_id)
        state = await run_pipeline(
            OnboardingState(document_type="menu", files=ingested, existing_menu=existing)
        )
        block = state.get("menu") or MenuBlock(status="couldnt_parse")
        block = _rewrite_source_urls(onboarding_id, block)
        row.menu = block.model_dump()
        self._emit_parse_events(onboarding_id, row, "menu", state)
        self._session.add(row)
        self._session.commit()
        # skipped_duplicates is a parse-time-only signal; it is not persisted on the row.
        block.skipped_duplicates = skipped_duplicates or None
        return block

    def _mark_block_parsing(self, row: OnboardingRow, block_name: str, block_dump: dict) -> None:
        # An unexpected error in the detached task reconciles the block to couldnt_parse
        # (see _run_detached). Only a process restart mid-parse can leave a block stuck in
        # "parsing"; the client resolves that via a poll timeout, and a durable worker queue
        # would reconcile it server-side.
        block_dump = dict(block_dump)
        block_dump["status"] = "parsing"
        setattr(row, block_name, block_dump)
        self._session.add(row)
        self._session.commit()

    def _mark_block_failed(self, onboarding_id: str, block_name: str) -> None:
        # Defensive reconciliation: if the detached parse raised before writing a result
        # block, flip it out of "parsing" so the client never polls a permanently stuck block.
        self._session.rollback()
        try:
            row = self._require(onboarding_id)
        except OnboardingNotFoundError:
            return
        block_dump = dict(getattr(row, block_name) or {})
        block_dump["status"] = "couldnt_parse"
        setattr(row, block_name, block_dump)
        self._session.add(row)
        self._session.commit()

    def save_legal(self, onboarding_id: str, block: LegalBlock) -> LegalBlock:
        row = self._require(onboarding_id)
        _revalidate_legal(block)
        self._emit_validation_events(onboarding_id, row, _legal_validations(block))
        row.legal = block.model_dump()
        self._session.add(row)
        self._session.commit()
        return block

    def save_banking(self, onboarding_id: str, block: BankingBlock) -> BankingBlock:
        row = self._require(onboarding_id)
        existing_legal = LegalBlock.model_validate(row.legal or {})
        _revalidate_banking(block, existing_legal)
        self._emit_validation_events(onboarding_id, row, _banking_validations(block))
        row.banking = block.model_dump()
        self._session.add(row)
        self._session.commit()
        return block

    def save_menu(self, onboarding_id: str, block: MenuBlock) -> MenuBlock:
        row = self._require(onboarding_id)
        block = _rewrite_source_urls(onboarding_id, block)
        # skipped_duplicates is a parse-only signal; never persist it from an edit.
        block.skipped_duplicates = None
        row.menu = block.model_dump()
        self._session.add(row)
        self._session.commit()
        return block

    def confirm(self, onboarding_id: str, step: int) -> Onboarding:
        row = self._require(onboarding_id)
        confirmed = dict(row.confirmed or {})
        if step == 1:
            confirmed["legal"] = True
        elif step == 2:
            confirmed["banking"] = True
        elif step == 3:
            confirmed["menu"] = True
        row.confirmed = confirmed
        row.step = min(max(row.step, step + 1), 4)
        # The lifecycle events step_viewed / step_confirmed / onboarding_completed are owned
        # by the client; the friction median and TTV are derived server-side from their
        # created_at timestamps. The server emits only parse_completed,
        # registry_verification_result and validation_result.
        self._session.add(row)
        self._session.commit()
        return self._to_schema(row)

    def feedback(self, onboarding_id: str, csat: int, answers: dict) -> None:
        row = self._require(onboarding_id)
        row.csat = csat
        row.feedback_submitted = True
        row.feedback_at = datetime.now(UTC)
        analytics.track(
            self._session,
            kind="feedback_submitted",
            onboarding_id=onboarding_id,
            device=row.device,
            locale=row.locale,
            props={"csat": csat, "answers": answers},
        )
        self._session.add(row)
        self._session.commit()

    def publish(self, onboarding_id: str) -> Onboarding:
        row = self._require(onboarding_id)
        row.published = True
        self._session.add(row)
        self._session.commit()
        return self._to_schema(row)

    def assemble_restaurant(self, onboarding_id: str) -> Onboarding:
        return self._to_schema(self._require(onboarding_id))

    def get_stored_file(self, onboarding_id: str, file_id: str) -> StoredFile | None:
        return (
            self._session.query(StoredFile)
            .filter(StoredFile.onboarding_id == onboarding_id, StoredFile.id == file_id)
            .one_or_none()
        )

    def admin_onboardings(self) -> list[AdminOnboardingRow]:
        return analytics.admin_onboardings(self._session)

    def admin_metrics(self) -> AdminMetrics:
        return analytics.admin_metrics(self._session)

    def _require(self, onboarding_id: str) -> OnboardingRow:
        row = self._session.get(OnboardingRow, onboarding_id)
        if row is None:
            raise OnboardingNotFoundError(onboarding_id)
        return row

    def _store_and_ingest(
        self,
        onboarding_id: str,
        files: list[UploadFile],
        dedupe: bool = False,
        active_file_ids: list[str] | None = None,
    ) -> StoreResult:
        ingested: list[IngestedFile] = []
        skipped: list[str] = []
        known_hashes = self._known_content_hashes(active_file_ids or []) if dedupe else set()

        for upload in files:
            content_hash = hashlib.sha256(upload.content).hexdigest()
            if dedupe and content_hash in known_hashes:
                # Identical file already uploaded to this onboarding: don't store it,
                # don't ingest it, and don't send it to the model.
                skipped.append(upload.filename)
                continue
            known_hashes.add(content_hash)

            file_id = storage.new_file_id()
            result = ingest_file(file_id, upload.filename, upload.media_type, upload.content)
            path = storage.save_file(onboarding_id, file_id, upload.content)
            self._session.add(
                StoredFile(
                    id=file_id,
                    onboarding_id=onboarding_id,
                    filename=result.filename,
                    media_type=result.media_type,
                    kind=result.kind,
                    path=path,
                    content_hash=content_hash,
                )
            )
            analytics.track(
                self._session,
                kind="file_uploaded",
                onboarding_id=onboarding_id,
                props={"file_type": result.kind, "bytes": len(upload.content)},
            )
            ingested.append(result)
        self._session.flush()
        return StoreResult(ingested=ingested, skipped_duplicates=skipped)

    def _known_content_hashes(self, file_ids: list[str]) -> set[str]:
        # Dedupe only against files CURRENTLY in the menu, not the whole upload history,
        # so a file the owner deleted can be uploaded again.
        if not file_ids:
            return set()
        rows = (
            self._session.query(StoredFile.content_hash)
            .filter(
                StoredFile.id.in_(file_ids),
                StoredFile.content_hash.isnot(None),
            )
            .all()
        )
        return {row[0] for row in rows}

    def _emit_parse_events(
        self, onboarding_id: str, row: OnboardingRow, doc_type: str, state: OnboardingState
    ) -> None:
        for usage in state.get("usages", []):
            cost_flag = usage.cost_eur > settings.cost_cap_eur
            analytics.track(
                self._session,
                kind="parse_completed",
                onboarding_id=onboarding_id,
                device=row.device,
                locale=row.locale,
                props={
                    "step": doc_type,
                    "doc_type": doc_type,
                    "model": usage.model,
                    "tokens_in": usage.tokens_in,
                    "tokens_out": usage.tokens_out,
                    "latency_ms": usage.latency_ms,
                    "cost_eur": usage.cost_eur,
                    "over_cost_cap": cost_flag,
                },
            )
        registry_result = state.get("registry_result")
        if registry_result is not None:
            analytics.track(
                self._session,
                kind="registry_verification_result",
                onboarding_id=onboarding_id,
                device=row.device,
                locale=row.locale,
                props={
                    "identifier_type": "siren",
                    "lookup_status": registry_result.get("status"),
                    "name_match": registry_result.get("name_match"),
                    "latency_ms": registry_result.get("latency_ms"),
                    "cached": registry_result.get("cached"),
                },
            )

    def _emit_validation_events(
        self,
        onboarding_id: str,
        row: OnboardingRow,
        validations: list[tuple[str, str, bool | None]],
    ) -> None:
        for validator, field_name, passed in validations:
            if passed is None:
                continue
            analytics.track(
                self._session,
                kind="validation_result",
                onboarding_id=onboarding_id,
                device=row.device,
                locale=row.locale,
                props={"validator": validator, "field_name": field_name, "passed": passed},
            )

    def _to_schema(self, row: OnboardingRow) -> Onboarding:
        menu = MenuBlock.model_validate(row.menu or {})
        # skipped_duplicates is a parse-time-only signal; never surface it on a full read.
        menu.skipped_duplicates = None
        return Onboarding(
            id=row.id,
            created_at=row.created_at.isoformat(),
            updated_at=row.updated_at.isoformat(),
            locale=row.locale,
            device=row.device,
            step=row.step,
            confirmed=Confirmed.model_validate(row.confirmed or {}),
            published=bool(row.published),
            feedback_submitted=bool(row.feedback_submitted),
            csat=row.csat,
            legal=LegalBlock.model_validate(row.legal or {}),
            banking=BankingBlock.model_validate(row.banking or {}),
            menu=menu,
        )


async def _run_detached(
    onboarding_id: str,
    block_name: str,
    work: Callable[["OnboardingService"], Awaitable[_BlockT]],
) -> _BlockT:
    # The AI work runs in a DETACHED task with its OWN db session, bound to the same
    # engine/sessionmaker as the app and tests (SessionLocal). Detaching via create_task
    # means a client disconnect/refresh cancels only the awaiting request, not the task:
    # it runs to completion and writes the result block, so a reloaded page can poll the
    # row and still see parsing -> ready/couldnt_parse. Any unexpected error reconciles the
    # block to couldnt_parse so it never stays stuck in "parsing".
    async def runner() -> _BlockT:
        session = SessionLocal()
        service = OnboardingService(session)
        try:
            return await work(service)
        except Exception:
            service._mark_block_failed(onboarding_id, block_name)
            raise
        finally:
            session.close()

    return await asyncio.shield(asyncio.create_task(runner()))


def _preserve_legal(existing: LegalBlock, parsed: LegalBlock) -> LegalBlock:
    if existing.status == "empty":
        return parsed
    for name in existing.fields.model_fields:
        existing_field = getattr(existing.fields, name)
        if existing_field.provenance in PRESERVED_PROVENANCE and existing_field.value:
            setattr(parsed.fields, name, existing_field)
    return parsed


def _preserve_banking(existing: BankingBlock, parsed: BankingBlock) -> BankingBlock:
    if existing.status == "empty":
        return parsed
    for name in existing.fields.model_fields:
        existing_field = getattr(existing.fields, name)
        if existing_field.provenance in PRESERVED_PROVENANCE and existing_field.value:
            setattr(parsed.fields, name, existing_field)
    return parsed


def _rewrite_source_urls(onboarding_id: str, block: MenuBlock) -> MenuBlock:
    rewritten: list[SourceFile] = []
    for source in block.source_files:
        rewritten.append(
            source.model_copy(update={"url": f"/api/onboarding/{onboarding_id}/files/{source.id}"})
        )
    block.source_files = rewritten
    return block


def _revalidate_legal(block: LegalBlock) -> None:
    fields = block.fields
    fields.siren.valid = validate_siren(fields.siren.value) if fields.siren.value else None
    fields.siret.valid = validate_siret(fields.siret.value) if fields.siret.value else None


def _revalidate_banking(block: BankingBlock, legal: LegalBlock) -> None:
    fields = block.fields
    fields.iban.valid = validate_iban(fields.iban.value) if fields.iban.value else None
    fields.bic.valid = validate_bic(fields.bic.value) if fields.bic.value else None
    legal_name = legal.fields.legal_name.value
    block.cross_doc_holder_match = holder_matches_legal_name(
        fields.account_holder.value, legal_name
    )


def _legal_validations(block: LegalBlock) -> list[tuple[str, str, bool | None]]:
    return [
        ("siren_luhn", "siren", block.fields.siren.valid),
        ("siret_luhn", "siret", block.fields.siret.valid),
    ]


def _banking_validations(block: BankingBlock) -> list[tuple[str, str, bool | None]]:
    return [
        ("iban_mod97", "iban", block.fields.iban.valid),
        ("bic_format", "bic", block.fields.bic.valid),
        ("cross_doc_holder", "account_holder", block.cross_doc_holder_match),
    ]
