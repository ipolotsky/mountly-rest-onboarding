import pytest

from app import parsers, registry
from app.graph import OnboardingState, run_pipeline
from app.ingest import IngestedFile
from app.llm import ContentBlock, ParseResult, ParseUsage
from app.registry import RegistryResult
from app.schemas import MenuBlock


@pytest.fixture
def patched_llm(monkeypatch, legal_extraction, banking_extraction, menu_extraction):
    async def fake_extract(model, output_model, blocks, instruction, max_tokens=4096):
        if output_model is parsers._LegalExtraction:
            data = legal_extraction
        elif output_model is parsers._BankingExtraction:
            data = banking_extraction
        elif output_model is parsers._MenuExtraction:
            data = menu_extraction
        else:
            data = None
        usage = ParseUsage(model=model, tokens_in=1000, tokens_out=500, cost_eur=0.01)
        return ParseResult(status="ok", data=data, usage=usage)

    monkeypatch.setattr(parsers, "extract", fake_extract)


@pytest.fixture
def patched_registry(monkeypatch):
    async def fake_verify(siren, legal_name):
        return RegistryResult(
            status="match", name_match=True, matched_name="SAVEURS DU SOLEIL LEVANT"
        )

    monkeypatch.setattr(registry, "verify_siren", fake_verify)


def _ingested(kind="pdf", file_id="file_1"):
    role = "document" if kind == "pdf" else "image"
    media = "application/pdf" if kind == "pdf" else "image/jpeg"
    return IngestedFile(
        file_id=file_id,
        filename=f"{file_id}.{ 'pdf' if kind == 'pdf' else 'jpg'}",
        media_type=media,
        kind=kind,
        block=ContentBlock(role=role, media_type=media, data="QQ=="),
    )


async def test_legal_pipeline_produces_ready_block_with_validation(patched_llm, patched_registry):
    state = await run_pipeline(
        OnboardingState(document_type="legal", files=[_ingested()])
    )
    legal = state["legal"]
    assert legal.status == "ready"
    assert legal.fields.legal_name.value == "SAVEURS DU SOLEIL LEVANT"
    assert legal.fields.siren.value == "913472056"
    assert legal.fields.siren.valid is True
    assert legal.fields.legal_form.value == "SAS"
    assert legal.fields.legal_representative.value == "MORAND Céline"
    # SIRET is not printed on the Kbis -> missing placeholder.
    assert legal.fields.siret.value is None
    assert legal.fields.siret.status == "missing"
    assert legal.registry.status == "match"
    assert legal.registry.name_match is True


async def test_banking_pipeline_validates_and_cross_checks(patched_llm):
    legal_state = await run_pipeline(OnboardingState(document_type="legal", files=[_ingested()]))
    legal = legal_state["legal"]
    state = await run_pipeline(
        OnboardingState(
            document_type="banking",
            files=[_ingested()],
            existing_legal=legal,
        )
    )
    banking = state["banking"]
    assert banking.status == "ready"
    assert banking.fields.iban.value == "FR7618306000457021845630174"
    assert banking.fields.iban.valid is True
    assert banking.fields.bic.value == "AGRIFRPP878"
    assert banking.fields.bic.valid is True
    assert banking.cross_doc_holder_match is True


async def test_menu_pipeline_merges_groups_and_keeps_bucket(patched_llm):
    state = await run_pipeline(
        OnboardingState(
            document_type="menu",
            files=[_ingested(kind="image")],
            existing_menu=MenuBlock(),
        )
    )
    menu = state["menu"]
    assert menu.status == "ready"
    group_names = [group.name for group in menu.groups]
    assert "PIZZAS" in group_names
    assert len([name for name in group_names]) >= 4
    pizzas = next(group for group in menu.groups if group.name == "PIZZAS")
    assert len(pizzas.items) == 13
    # No empty "Sans catégorie" bucket is added when everything is categorized.
    assert [group for group in menu.groups if group.name == "Sans catégorie" and not group.items] == []


async def test_menu_reparse_does_not_duplicate_existing_items(patched_llm):
    first = (await run_pipeline(
        OnboardingState(
            document_type="menu",
            files=[_ingested(kind="image", file_id="file_a")],
            existing_menu=MenuBlock(),
        )
    ))["menu"]
    second = (await run_pipeline(
        OnboardingState(
            document_type="menu",
            files=[_ingested(kind="image", file_id="file_b")],
            existing_menu=first,
        )
    ))["menu"]
    pizzas = next(group for group in second.groups if group.name == "PIZZAS")
    assert len(pizzas.items) == 13


async def test_registry_failure_keeps_legal_ready(monkeypatch, patched_llm):
    async def failing_verify(siren, legal_name):
        return RegistryResult(status="unavailable", name_match=None)

    monkeypatch.setattr(registry, "verify_siren", failing_verify)
    state = await run_pipeline(OnboardingState(document_type="legal", files=[_ingested()]))
    legal = state["legal"]
    assert legal.status == "ready"
    assert legal.registry.status == "unavailable"
