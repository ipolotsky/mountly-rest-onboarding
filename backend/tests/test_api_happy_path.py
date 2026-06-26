import io

import pytest

from app import parsers, registry
from app.llm import ParseResult, ParseUsage
from app.registry import RegistryResult


@pytest.fixture(autouse=True)
def patched_ai(monkeypatch, legal_extraction, banking_extraction, menu_extraction):
    async def fake_extract(model, output_model, blocks, instruction, max_tokens=4096):
        if output_model is parsers._LegalExtraction:
            data = legal_extraction
        elif output_model is parsers._BankingExtraction:
            data = banking_extraction
        elif output_model is parsers._MenuExtraction:
            data = menu_extraction
        else:
            data = None
        usage = ParseUsage(model=model, tokens_in=1200, tokens_out=400, cost_eur=0.012)
        return ParseResult(status="ok", data=data, usage=usage)

    async def fake_verify(siren, legal_name):
        return RegistryResult(status="match", name_match=True)

    monkeypatch.setattr(parsers, "extract", fake_extract)
    monkeypatch.setattr(registry, "verify_siren", fake_verify)


def _pdf(name: str) -> tuple[str, io.BytesIO, str]:
    return (name, io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")


def _image(name: str) -> tuple[str, io.BytesIO, str]:
    return (name, io.BytesIO(b"\x89PNG fake"), "image/png")


def _confirm(client, onboarding_id: str, step: int) -> None:
    response = client.post(f"/api/onboarding/{onboarding_id}/confirm", json={"step": step})
    assert response.status_code == 200


def test_full_happy_path(client):
    created = client.post("/api/onboarding", json={"locale": "fr", "device": "mobile"})
    assert created.status_code == 200
    onboarding_id = created.json()["id"]

    legal = client.post(
        f"/api/onboarding/{onboarding_id}/legal/parse",
        files={"files": _pdf("kbis.pdf")},
    )
    assert legal.status_code == 200
    legal_body = legal.json()
    assert legal_body["status"] == "ready"
    assert legal_body["fields"]["siren"]["value"] == "913472056"
    assert legal_body["fields"]["siren"]["valid"] is True
    assert legal_body["registry"]["status"] == "match"

    _confirm(client, onboarding_id, 1)

    banking = client.post(
        f"/api/onboarding/{onboarding_id}/banking/parse",
        files={"files": _pdf("rib.pdf")},
    )
    assert banking.status_code == 200
    banking_body = banking.json()
    assert banking_body["status"] == "ready"
    assert banking_body["fields"]["iban"]["valid"] is True
    assert banking_body["cross_doc_holder_match"] is True

    _confirm(client, onboarding_id, 2)

    menu = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("menu.png")},
    )
    assert menu.status_code == 200
    menu_body = menu.json()
    assert menu_body["status"] == "ready"
    assert len(menu_body["groups"]) >= 4
    source = menu_body["source_files"][0]
    assert source["url"] == f"/api/onboarding/{onboarding_id}/files/{source['id']}"

    _confirm(client, onboarding_id, 3)

    final = client.get(f"/api/onboarding/{onboarding_id}/restaurant")
    assert final.status_code == 200
    final_body = final.json()
    assert final_body["step"] == 4
    assert final_body["confirmed"] == {"legal": True, "banking": True, "menu": True}


def test_served_file_round_trips(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    menu = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("menu.png")},
    )
    source = menu.json()["source_files"][0]
    served = client.get(source["url"])
    assert served.status_code == 200
    assert served.content == b"\x89PNG fake"


def test_feedback_and_events(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    feedback = client.post(
        f"/api/onboarding/{onboarding_id}/feedback",
        json={"csat": 5, "answers": {"reason": "fast"}},
    )
    assert feedback.status_code == 200
    assert feedback.json() == {"ok": True}

    events = client.post(
        "/api/events",
        json={
            "events": [
                {
                    "name": "step_viewed",
                    "onboarding_id": onboarding_id,
                    "session_id": "s1",
                    "device": "mobile",
                    "locale": "fr",
                    "schema_version": 1,
                    "ts": "2026-01-01T00:00:00Z",
                    "props": {"step": 1},
                }
            ]
        },
    )
    assert events.status_code == 200


def test_admin_endpoints_return_shapes(client):
    onboarding_id = client.post("/api/onboarding", json={"device": "desktop"}).json()["id"]
    client.post(
        f"/api/onboarding/{onboarding_id}/legal/parse", files={"files": _pdf("kbis.pdf")}
    )

    rows = client.get("/api/admin/onboardings")
    assert rows.status_code == 200
    assert isinstance(rows.json(), list)
    assert rows.json()[0]["id"] == onboarding_id

    metrics = client.get("/api/admin/metrics")
    assert metrics.status_code == 200
    body = metrics.json()
    assert {"funnel", "ai_cost", "quality", "friction"} <= set(body.keys())
    assert any(stage["step"] == "started" for stage in body["funnel"])


def test_missing_onboarding_is_404(client):
    assert client.get("/api/onboarding/does-not-exist").status_code == 404
