import asyncio

import pytest

from app import parsers, registry
from app.database import SessionLocal
from app.ingest import ingest_file
from app.llm import ParseResult, ParseUsage
from app.models import Onboarding as OnboardingRow
from app.registry import RegistryResult
from app.service import OnboardingService, UploadFile

LEGAL = {
    "legal_name": "SAVEURS DU SOLEIL LEVANT",
    "legal_name_confidence": 0.98,
    "siren": "913472056",
    "siren_confidence": 0.97,
    "siret": None,
    "siret_confidence": None,
    "legal_form": "SAS",
    "legal_form_confidence": 0.9,
    "registered_address": "18 Route du Palais des Sports 74110 Morzine",
    "registered_address_confidence": 0.93,
    "legal_representative": "MORAND Céline",
    "legal_representative_confidence": 0.95,
}


def _read_status(onboarding_id: str, block: str) -> str:
    # A fresh session, exactly like a separate GET request would use.
    with SessionLocal() as session:
        onboarding = OnboardingService(session).get(onboarding_id)
    return getattr(onboarding, block).status


async def test_block_passes_through_parsing_then_ready(fresh_database, monkeypatch):
    gate = asyncio.Event()

    async def gated_extract(model, output_model, blocks, instruction, max_tokens=4096):
        await gate.wait()
        usage = ParseUsage(model=model, tokens_in=10, tokens_out=5, cost_eur=0.0)
        return ParseResult(status="ok", data=LEGAL, usage=usage)

    async def fake_verify(siren, legal_name):
        return RegistryResult(status="match", name_match=True)

    monkeypatch.setattr(parsers, "extract", gated_extract)
    monkeypatch.setattr(registry, "verify_siren", fake_verify)

    with SessionLocal() as session:
        onboarding_id = OnboardingService(session).create("fr", "mobile")

    ingest_file("setup", "k.pdf", "application/pdf", b"%PDF-1.4")
    upload = UploadFile("k.pdf", "application/pdf", b"%PDF-1.4 fake")

    with SessionLocal() as session:
        parse_task = asyncio.create_task(
            OnboardingService(session).parse_legal(onboarding_id, [upload])
        )

        # The extract is gated, so the parse is in flight: the row must read "parsing"
        # from any concurrent GET, even though the AI work has not produced a result yet.
        for _ in range(200):
            if _read_status(onboarding_id, "legal") == "parsing":
                break
            await asyncio.sleep(0.005)
        assert _read_status(onboarding_id, "legal") == "parsing"

        # Release the model call; the awaited parse returns the final ready block.
        gate.set()
        block = await parse_task

    assert block.status == "ready"
    assert block.fields.siren.value == "913472056"
    assert block.fields.siren.valid is True
    # The persisted row resolved to ready too (the bg task's own session wrote it).
    assert _read_status(onboarding_id, "legal") == "ready"


async def test_detached_task_completes_even_if_await_is_cancelled(fresh_database, monkeypatch):
    started = asyncio.Event()
    release = asyncio.Event()

    async def gated_extract(model, output_model, blocks, instruction, max_tokens=4096):
        started.set()
        await release.wait()
        usage = ParseUsage(model=model, tokens_in=10, tokens_out=5, cost_eur=0.0)
        return ParseResult(status="ok", data=LEGAL, usage=usage)

    async def fake_verify(siren, legal_name):
        return RegistryResult(status="match", name_match=True)

    monkeypatch.setattr(parsers, "extract", gated_extract)
    monkeypatch.setattr(registry, "verify_siren", fake_verify)

    with SessionLocal() as session:
        onboarding_id = OnboardingService(session).create("fr", "desktop")

    upload = UploadFile("k.pdf", "application/pdf", b"%PDF-1.4 fake")

    session = SessionLocal()
    parse_task = asyncio.create_task(
        OnboardingService(session).parse_legal(onboarding_id, [upload])
    )
    await started.wait()  # background task is in flight inside extract

    # Simulate a client disconnect: cancel the awaiting request mid-parse.
    parse_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await parse_task
    session.close()

    # The detached background task is NOT cancelled: release it and let it finish.
    release.set()
    for _ in range(200):
        if _read_status(onboarding_id, "legal") == "ready":
            break
        await asyncio.sleep(0.005)
    assert _read_status(onboarding_id, "legal") == "ready"


async def test_exception_in_parse_reconciles_block_to_couldnt_parse(fresh_database, monkeypatch):
    # llm.extract catches provider errors itself; here extract raises BEFORE that guard, so the
    # error escapes the pipeline. The detached task must reconcile the block out of "parsing"
    # to "couldnt_parse" rather than leaving it stuck forever.
    async def boom(model, output_model, blocks, instruction, max_tokens=4096):
        raise RuntimeError("simulated provider explosion outside the extract guard")

    monkeypatch.setattr(parsers, "extract", boom)

    with SessionLocal() as session:
        onboarding_id = OnboardingService(session).create("fr", "desktop")

    upload = UploadFile("k.pdf", "application/pdf", b"%PDF-1.4 fake")
    with SessionLocal() as session:
        with pytest.raises(RuntimeError):
            await OnboardingService(session).parse_legal(onboarding_id, [upload])

    assert _read_status(onboarding_id, "legal") == "couldnt_parse"


async def test_two_detached_parses_do_not_clobber_each_other(fresh_database, monkeypatch):
    banking_data = {
        "account_holder": "SAVEURS DU SOLEIL LEVANT",
        "account_holder_confidence": 0.9,
        "bank_name": "CA",
        "bank_name_confidence": 0.9,
        "iban": "FR7618306000457021845630174",
        "iban_confidence": 0.9,
        "bic": "AGRIFRPP878",
        "bic_confidence": 0.9,
    }

    async def fake_extract(model, output_model, blocks, instruction, max_tokens=4096):
        data = LEGAL if output_model is parsers._LegalExtraction else banking_data
        return ParseResult(status="ok", data=data, usage=ParseUsage(model=model, cost_eur=0.01))

    async def fake_verify(siren, legal_name):
        return RegistryResult(status="match", name_match=True)

    monkeypatch.setattr(parsers, "extract", fake_extract)
    monkeypatch.setattr(registry, "verify_siren", fake_verify)

    upload = UploadFile("k.pdf", "application/pdf", b"%PDF-1.4 fake")
    with SessionLocal() as session:
        onboarding_id = OnboardingService(session).create("fr", "desktop")
    with SessionLocal() as session:
        legal = await OnboardingService(session).parse_legal(onboarding_id, [upload])
    with SessionLocal() as session:
        banking = await OnboardingService(session).parse_banking(onboarding_id, [upload])

    assert legal.status == "ready"
    assert banking.status == "ready"
    with SessionLocal() as session:
        row = session.get(OnboardingRow, onboarding_id)
        assert row.legal["fields"]["siren"]["value"] == "913472056"
        assert row.banking["fields"]["iban"]["value"] == "FR7618306000457021845630174"
