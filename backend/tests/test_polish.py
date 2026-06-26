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

MENU = {
    "groups": [
        {
            "name": "PIZZAS",
            "items": [
                {"name": "Margarita", "prices": [{"label": None, "amount": "10.00€"}],
                 "confidence": 0.95},
                {"name": "Regina", "prices": [{"label": None, "amount": "15.00€"}],
                 "confidence": 0.95},
            ],
        }
    ]
}


@pytest.fixture(autouse=True)
def patched_ai(monkeypatch):
    def fake_extract(model, output_model, blocks, instruction, max_tokens=4096):
        if output_model is parsers._LegalExtraction:
            data = LEGAL
        elif output_model is parsers._MenuExtraction:
            data = MENU
        else:
            data = None
        usage = ParseUsage(model=model, tokens_in=900, tokens_out=300, cost_eur=0.01)
        return ParseResult(status="ok", data=data, usage=usage)

    monkeypatch.setattr(parsers, "extract", fake_extract)
    monkeypatch.setattr(
        registry, "verify_siren", lambda s, n: RegistryResult(status="match", name_match=True)
    )


def _pdf(name: str):
    return (name, io.BytesIO(b"%PDF-1.4 menu fake"), "application/pdf")


def _image(name: str, payload: bytes = b"\x89PNG identical-bytes"):
    return (name, io.BytesIO(payload), "image/png")


# --- #15: admin dashboard 500 regression -------------------------------------------------


def test_admin_onboardings_survives_duplicate_lifecycle_events(client):
    from app.database import SessionLocal
    from app.models import Event, Onboarding

    with SessionLocal() as session:
        session.add(Onboarding(id="resumed", locale="fr", device="mobile", step=4))
        for _ in range(2):
            session.add(Event(kind="onboarding_started", onboarding_id="resumed", props={}))
            session.add(Event(kind="onboarding_completed", onboarding_id="resumed", props={}))
        session.commit()

    # Before the fix this raised MultipleResultsFound and 500'd the whole dashboard.
    response = client.get("/api/admin/onboardings")
    assert response.status_code == 200
    assert any(row["id"] == "resumed" for row in response.json())


# --- #14: feedback persistence -----------------------------------------------------------


def test_feedback_persists_on_onboarding(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]

    before = client.get(f"/api/onboarding/{onboarding_id}").json()
    assert before["feedback_submitted"] is False
    assert before["csat"] is None

    posted = client.post(
        f"/api/onboarding/{onboarding_id}/feedback",
        json={"csat": 4, "answers": {"reason": "clear"}},
    )
    assert posted.status_code == 200

    after = client.get(f"/api/onboarding/{onboarding_id}").json()
    assert after["feedback_submitted"] is True
    assert after["csat"] == 4

    rows = client.get("/api/admin/onboardings").json()
    row = next(row for row in rows if row["id"] == onboarding_id)
    assert row["csat"] == 4


# --- publish endpoint --------------------------------------------------------------------


def test_publish_sets_published_flag(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    assert client.get(f"/api/onboarding/{onboarding_id}").json()["published"] is False

    published = client.post(f"/api/onboarding/{onboarding_id}/publish")
    assert published.status_code == 200
    assert published.json()["published"] is True

    # Survives a reload.
    assert client.get(f"/api/onboarding/{onboarding_id}").json()["published"] is True


def test_publish_missing_onboarding_is_404(client):
    assert client.post("/api/onboarding/nope/publish").status_code == 404


# --- #5: menu dedupe by content hash -----------------------------------------------------


def test_menu_reupload_is_deduped_by_content_hash(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    payload = b"\x89PNG the-same-menu-bytes"

    first = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("menu.png", payload)},
    ).json()
    assert first["status"] == "ready"
    pizzas_first = next(group for group in first["groups"] if group["name"] == "PIZZAS")
    assert len(pizzas_first["items"]) == 2
    assert first.get("skipped_duplicates") in (None, [])

    # Re-upload the byte-identical file under a different name.
    second = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("menu-copy.png", payload)},
    ).json()
    assert second["skipped_duplicates"] == ["menu-copy.png"]
    pizzas_second = next(group for group in second["groups"] if group["name"] == "PIZZAS")
    # Items are NOT duplicated by the re-upload.
    assert len(pizzas_second["items"]) == 2


def test_deleted_menu_file_can_be_reuploaded(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    payload = b"\x89PNG reuploadable-bytes"

    client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("menu.png", payload)},
    )
    # Owner deletes the file (client-side: drop it from source_files, then PUT the menu).
    menu = client.get(f"/api/onboarding/{onboarding_id}").json()["menu"]
    menu["source_files"] = []
    client.put(f"/api/onboarding/{onboarding_id}/menu", json=menu)

    # The same bytes can now be uploaded again — a deleted file is no longer a "duplicate".
    again = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("menu.png", payload)},
    ).json()
    assert again.get("skipped_duplicates") in (None, [])
    assert again["status"] == "ready"


def test_distinct_menu_files_are_not_deduped(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    first = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("a.png", b"\x89PNG aaa")},
    ).json()
    assert first.get("skipped_duplicates") in (None, [])
    second = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("b.png", b"\x89PNG bbb-different")},
    ).json()
    assert second.get("skipped_duplicates") in (None, [])


def test_get_onboarding_never_exposes_skipped_duplicates(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    payload = b"\x89PNG dup-bytes"
    client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("m.png", payload)},
    )
    client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _image("m2.png", payload)},
    )
    full = client.get(f"/api/onboarding/{onboarding_id}").json()
    assert full["menu"]["skipped_duplicates"] is None


# --- #9: PDF menu parses ------------------------------------------------------------------


def test_menu_accepts_pdf_file(client):
    onboarding_id = client.post("/api/onboarding", json={}).json()["id"]
    response = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse",
        files={"files": _pdf("menu.pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert any(group["name"] == "PIZZAS" for group in body["groups"])
    source = body["source_files"][0]
    assert source["kind"] == "pdf"
