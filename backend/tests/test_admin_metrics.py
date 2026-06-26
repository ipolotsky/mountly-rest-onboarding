import io

import pytest

from app import parsers, registry
from app.llm import ParseResult, ParseUsage
from app.registry import RegistryResult

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

BANKING = {
    "account_holder": "SAVEURS DU SOLEIL LEVANT",
    "account_holder_confidence": 0.97,
    "bank_name": "Crédit Agricole des Savoie",
    "bank_name_confidence": 0.94,
    "iban": "FR7618306000457021845630174",
    "iban_confidence": 0.99,
    "bic": "AGRIFRPP878",
    "bic_confidence": 0.96,
}


@pytest.fixture(autouse=True)
def patched_ai(monkeypatch):
    def fake_extract(model, output_model, blocks, instruction, max_tokens=4096):
        if output_model is parsers._LegalExtraction:
            data = LEGAL
        elif output_model is parsers._BankingExtraction:
            data = BANKING
        else:
            data = None
        usage = ParseUsage(model=model, tokens_in=1000, tokens_out=500, cost_eur=0.01)
        return ParseResult(status="ok", data=data, usage=usage)

    monkeypatch.setattr(parsers, "extract", fake_extract)
    monkeypatch.setattr(
        registry, "verify_siren", lambda s, n: RegistryResult(status="match", name_match=True)
    )


def _pdf(name: str):
    return (name, io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")


def _emit_field_resolved(client, onboarding_id, doc_type, resolutions):
    events = [
        {
            "name": "field_resolved",
            "onboarding_id": onboarding_id,
            "session_id": "s1",
            "device": "mobile",
            "locale": "fr",
            "schema_version": 1,
            "ts": "2026-01-01T00:00:00Z",
            "props": {
                "doc_type": doc_type,
                "field_name": f"f{index}",
                "parsed_value_present": True,
                "resolution": resolution,
            },
        }
        for index, resolution in enumerate(resolutions)
    ]
    assert client.post("/api/events", json={"events": events}).status_code == 200


def test_funnel_uses_outcome_based_labels(client):
    onboarding_id = client.post("/api/onboarding", json={"device": "mobile"}).json()["id"]
    client.post(f"/api/onboarding/{onboarding_id}/legal/parse", files={"files": _pdf("k.pdf")})
    client.post(f"/api/onboarding/{onboarding_id}/confirm", json={"step": 1})

    funnel = {stage["step"]: stage for stage in client.get("/api/admin/metrics").json()["funnel"]}
    assert set(funnel.keys()) == {
        "started",
        "legal_done",
        "banking_done",
        "menu_done",
        "publishable",
    }
    assert funnel["started"]["mobile"] == 1
    assert funnel["legal_done"]["mobile"] == 1
    assert funnel["banking_done"]["mobile"] == 0


def test_auto_fill_acceptance_buckets_by_doc_type(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    # 3 legal fields, 2 accepted as-is -> 2/3. 2 banking fields, both accepted -> 1.0.
    _emit_field_resolved(
        client, onboarding_id, "legal", ["accepted_as_is", "accepted_as_is", "edited"]
    )
    _emit_field_resolved(client, onboarding_id, "banking", ["accepted_as_is", "accepted_as_is"])

    quality = client.get("/api/admin/metrics").json()["quality"]
    acceptance = quality["auto_fill_acceptance"]
    assert set(acceptance.keys()) == {"legal", "banking", "menu"}
    assert acceptance["legal"] == pytest.approx(2 / 3, abs=1e-4)
    assert acceptance["banking"] == 1.0
    assert acceptance["menu"] == 0.0


def test_friction_drop_off_is_a_ratio(client):
    # Two onboardings reach step 1; one advances past it, one stalls.
    stalled = client.post("/api/onboarding", json={}).json()["id"]
    advanced = client.post("/api/onboarding", json={}).json()["id"]
    client.post(f"/api/onboarding/{advanced}/legal/parse", files={"files": _pdf("k.pdf")})
    client.post(f"/api/onboarding/{advanced}/confirm", json={"step": 1})

    friction_stages = client.get("/api/admin/metrics").json()["friction"]
    friction = {stage["step"]: stage for stage in friction_stages}
    # Both are at/over step1; one advanced to step>=2 -> drop_off = (2-1)/2 = 0.5.
    assert 0.0 <= friction["step1"]["drop_off"] <= 1.0
    assert friction["step1"]["drop_off"] == pytest.approx(0.5, abs=1e-4)
    assert stalled != advanced


def test_confirm_does_not_emit_server_lifecycle_events(client):
    from app.models import Event

    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    client.post(f"/api/onboarding/{onboarding_id}/legal/parse", files={"files": _pdf("k.pdf")})
    client.post(f"/api/onboarding/{onboarding_id}/confirm", json={"step": 1})

    from app.database import SessionLocal

    with SessionLocal() as session:
        kinds = {event.kind for event in session.query(Event).all()}
    # The client owns step_confirmed / onboarding_completed; the server must not emit them.
    assert "step_confirmed" not in kinds
    assert "onboarding_completed" not in kinds
    assert "parse_completed" in kinds
    assert "registry_verification_result" in kinds


def test_save_legal_recomputes_valid_server_side(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    block = client.post(
        f"/api/onboarding/{onboarding_id}/legal/parse", files={"files": _pdf("k.pdf")}
    ).json()

    # Client lies: garbage SIREN flagged valid=true with user_edited provenance.
    block["fields"]["siren"]["value"] = "000000000"
    block["fields"]["siren"]["valid"] = True
    block["fields"]["siren"]["provenance"] = "user_edited"

    saved = client.put(f"/api/onboarding/{onboarding_id}/legal", json=block).json()
    assert saved["fields"]["siren"]["valid"] is False


def test_save_banking_recomputes_valid_and_cross_doc(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    client.post(f"/api/onboarding/{onboarding_id}/legal/parse", files={"files": _pdf("k.pdf")})
    block = client.post(
        f"/api/onboarding/{onboarding_id}/banking/parse", files={"files": _pdf("r.pdf")}
    ).json()

    # Client lies about a tampered IBAN.
    block["fields"]["iban"]["value"] = "FR7618306000457021845630175"
    block["fields"]["iban"]["valid"] = True
    saved = client.put(f"/api/onboarding/{onboarding_id}/banking", json=block).json()
    assert saved["fields"]["iban"]["valid"] is False
    # Holder still matches the legal name -> cross-doc match is recomputed True.
    assert saved["cross_doc_holder_match"] is True
