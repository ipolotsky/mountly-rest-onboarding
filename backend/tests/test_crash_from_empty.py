from app.database import SessionLocal
from app.llm import ParseResult, ParseUsage
from app.models import Onboarding as OnboardingRow
from app.parsers import _build_banking_block, _build_legal_block
from app.schemas import BankingBlock, LegalBlock, MenuBlock, Onboarding
from app.service import OnboardingService


def _failed_result() -> ParseResult:
    return ParseResult(status="couldnt_parse", data=None, usage=ParseUsage(model="x"))


def test_legal_block_from_failed_parse_renders_placeholders():
    block = _build_legal_block(_failed_result())
    assert block.status == "couldnt_parse"
    for name in block.fields.model_fields:
        field = getattr(block.fields, name)
        assert field.value is None
        assert field.status == "missing"


def test_banking_block_from_failed_parse_renders_placeholders():
    block = _build_banking_block(_failed_result())
    assert block.status == "couldnt_parse"
    for name in block.fields.model_fields:
        field = getattr(block.fields, name)
        assert field.value is None
        assert field.status == "missing"


def test_onboarding_assembles_from_fully_empty_state():
    onboarding = Onboarding(
        id="abc",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
        legal=LegalBlock(status="couldnt_parse"),
        banking=BankingBlock(status="couldnt_parse"),
        menu=MenuBlock(status="couldnt_parse"),
    )
    payload = onboarding.model_dump()

    assert payload["legal"]["status"] == "couldnt_parse"
    assert payload["legal"]["fields"]["legal_name"]["value"] is None
    assert payload["banking"]["fields"]["iban"]["value"] is None
    assert payload["menu"]["groups"] == []
    # Round-trips cleanly: the read-only restaurant page can always render this.
    assert Onboarding.model_validate(payload).id == "abc"


def test_empty_default_onboarding_is_renderable():
    onboarding = Onboarding(
        id="empty",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    assert onboarding.legal.status == "empty"
    assert onboarding.legal.fields.siren.value is None
    assert onboarding.banking.fields.bic.status == "missing"
    assert onboarding.menu.groups == []


def test_assemble_from_all_null_jsonb_row(fresh_database):
    # A row whose confirmed/legal/banking/menu JSONB columns are literally NULL (not the
    # schema defaults) must still render through get and assemble_restaurant, never raise.
    with SessionLocal() as session:
        session.add(
            OnboardingRow(
                id="null_row",
                locale="fr",
                device="desktop",
                step=1,
                confirmed=None,
                legal=None,
                banking=None,
                menu=None,
            )
        )
        session.commit()

    with SessionLocal() as session:
        service = OnboardingService(session)
        onboarding = service.get("null_row")
        assert onboarding.legal.status == "empty"
        assert onboarding.banking.fields.iban.value is None
        assert onboarding.menu.groups == []
        assert service.assemble_restaurant("null_row").id == "null_row"


def test_admin_from_all_null_jsonb_row_does_not_crash(fresh_database):
    with SessionLocal() as session:
        session.add(
            OnboardingRow(
                id="null_row2",
                locale="fr",
                device="mobile",
                step=1,
                confirmed=None,
                legal=None,
                banking=None,
                menu=None,
            )
        )
        session.commit()

    with SessionLocal() as session:
        service = OnboardingService(session)
        metrics = service.admin_metrics()
        rows = service.admin_onboardings()
    assert any(stage.step == "started" for stage in metrics.funnel)
    assert any(row.id == "null_row2" for row in rows)
