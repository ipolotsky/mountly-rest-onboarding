"""Independent multi-onboarding audit driven through the real HTTP surface.

Drives several distinct restaurants end to end via the in-process TestClient with
``parsers.extract`` and ``registry.verify_siren`` monkeypatched (no API key). Asserts block
statuses, validator results on the real identifiers, menu edits surviving, price/variant
preservation as strings, the undeletable bucket, and the admin aggregates across onboardings.
"""

import io

import pytest

from app import parsers, registry
from app.llm import ParseResult, ParseUsage
from app.registry import RegistryResult

KOYUKI_LEGAL = {
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

KOYUKI_BANKING = {
    "account_holder": "SAVEURS DU SOLEIL LEVANT",
    "account_holder_confidence": 0.97,
    "bank_name": "Crédit Agricole des Savoie",
    "bank_name_confidence": 0.94,
    "iban": "FR7618306000457021845630174",
    "iban_confidence": 0.99,
    "bic": "AGRIFRPP878",
    "bic_confidence": 0.96,
}

KOYUKI_MENU = {
    "groups": [
        {
            "name": "PIZZAS",
            "items": [
                {"name": "Margarita", "prices": [{"label": None, "amount": "10.00€"}],
                 "confidence": 0.95},
                {"name": "Funghi", "prices": [{"label": None, "amount": "13.00€"}],
                 "confidence": 0.95},
                {"name": "Regina", "prices": [{"label": None, "amount": "15.00€"}],
                 "confidence": 0.95},
            ],
        },
        {
            "name": "KEBAB",
            "items": [
                {"name": "Kebab Galette", "prices": [{"label": None, "amount": "8,50"}],
                 "confidence": 0.9},
                {"name": "Kebab Assiette", "prices": [{"label": None, "amount": "12,00"}],
                 "confidence": 0.9},
            ],
        },
        {
            "name": "TACOS",
            "items": [
                {"name": "Tacos 1 viande",
                 "prices": [{"label": "Menu", "amount": "9,00"},
                            {"label": "Seul", "amount": "7,00"}],
                 "confidence": 0.88},
            ],
        },
        {
            "name": "ASSIETTES",
            "items": [
                {"name": "Assiette Kebab", "prices": [{"label": None, "amount": "13,00"}],
                 "confidence": 0.86},
            ],
        },
    ]
}

# A real, valid second French entity (Le Comptoir Gourmet) — checksums must pass.
# SIREN 552081317 (a Luhn-valid identifier), IBAN FR1420041010050500013M02606 (mod-97 valid).
DRINKS_LEGAL = {
    "legal_name": "LE COMPTOIR GOURMET",
    "legal_name_confidence": 0.92,
    "siren": "552081317",
    "siren_confidence": 0.9,
    "siret": None,
    "siret_confidence": None,
    "legal_form": "SARL",
    "legal_form_confidence": 0.4,
    "registered_address": "12 Rue de la Soif 69001 Lyon",
    "registered_address_confidence": 0.8,
    "legal_representative": "DUPONT Jean",
    "legal_representative_confidence": 0.55,
}

DRINKS_BANKING = {
    "account_holder": "LE COMPTOIR GOURMET",
    "account_holder_confidence": 0.9,
    "bank_name": "La Banque Postale",
    "bank_name_confidence": 0.88,
    "iban": "FR1420041010050500013M02606",
    "iban_confidence": 0.97,
    "bic": "PSSTFRPPPAR",
    "bic_confidence": 0.9,
}

DRINKS_MENU = {
    "groups": [
        {
            "name": "BIERES",
            "items": [
                {"name": "Pression Blonde",
                 "prices": [{"label": "25 cl", "amount": "3,50"},
                            {"label": "50 cl", "amount": "6,00"}],
                 "confidence": 0.9},
                {"name": "IPA Artisanale",
                 "prices": [{"label": "25 cl", "amount": "4,50"},
                            {"label": "50 cl", "amount": "7,50"}],
                 "confidence": 0.85},
            ],
        },
        {
            "name": "VINS",
            "items": [
                {"name": "Côtes du Rhône",
                 "prices": [{"label": "Verre", "amount": "3 €"},
                            {"label": "Bouteille", "amount": "18 €"}],
                 "confidence": 0.8},
                {"name": "Chablis",
                 "prices": [{"label": "Verre", "amount": "5 €"},
                            {"label": "Bouteille", "amount": "32 €"}],
                 "confidence": 0.5},
            ],
        },
    ]
}

# Third restaurant: a price-less SAUCES section (empty prices) plus a normal section.
# Valid identifiers: SIREN 732829320 (Danone, Luhn-valid), IBAN FR7630006000011234567890189 (valid).
PRICELESS_LEGAL = {
    "legal_name": "BISTROT DES SAUCES",
    "legal_name_confidence": 0.95,
    "siren": "732829320",
    "siren_confidence": 0.95,
    "siret": "73282932000074",
    "siret_confidence": 0.9,
    "legal_form": "EURL",
    "legal_form_confidence": 0.85,
    "registered_address": "5 Place du Marché 33000 Bordeaux",
    "registered_address_confidence": 0.9,
    "legal_representative": "MARTIN Sophie",
    "legal_representative_confidence": 0.9,
}

PRICELESS_BANKING = {
    "account_holder": "BISTROT DES SAUCES",
    "account_holder_confidence": 0.93,
    "bank_name": "BNP Paribas",
    "bank_name_confidence": 0.9,
    "iban": "FR7630006000011234567890189",
    "iban_confidence": 0.95,
    "bic": "BNPAFRPPXXX",
    "bic_confidence": 0.9,
}

PRICELESS_MENU = {
    "groups": [
        {
            "name": "PLATS",
            "items": [
                {"name": "Burger Maison", "prices": [{"label": None, "amount": "14,00"}],
                 "confidence": 0.9},
            ],
        },
        {
            "name": "SAUCES",
            "items": [
                {"name": "Blanche", "prices": [], "confidence": 0.8},
                {"name": "Algérienne", "prices": [], "confidence": 0.8},
                {"name": "Samouraï", "prices": [], "confidence": 0.8},
            ],
        },
    ]
}


class _Dataset:
    """Holds the active per-restaurant extraction payloads for the monkeypatched extractor."""

    def __init__(self) -> None:
        self.legal: dict | None = None
        self.banking: dict | None = None
        self.menu: dict | None = None


@pytest.fixture
def dataset(monkeypatch):
    active = _Dataset()

    async def fake_extract(model, output_model, blocks, instruction, max_tokens=4096):
        if output_model is parsers._LegalExtraction:
            data = active.legal
        elif output_model is parsers._BankingExtraction:
            data = active.banking
        elif output_model is parsers._MenuExtraction:
            data = active.menu
        else:
            data = None
        status = "ok" if data is not None else "couldnt_parse"
        usage = ParseUsage(model=model, tokens_in=1500, tokens_out=600, cost_eur=0.02)
        return ParseResult(status=status, data=data, usage=usage)

    async def fake_verify(siren, legal_name):
        return RegistryResult(status="match", name_match=True, matched_name=legal_name)

    monkeypatch.setattr(parsers, "extract", fake_extract)
    monkeypatch.setattr(registry, "verify_siren", fake_verify)
    return active


def _pdf(name: str):
    return (name, io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")


def _image(name: str):
    return (name, io.BytesIO(b"\x89PNG fake-image-bytes"), "image/png")


def _confirm(client, onboarding_id: str, step: int) -> dict:
    response = client.post(f"/api/onboarding/{onboarding_id}/confirm", json={"step": step})
    assert response.status_code == 200, response.text
    return response.json()


def _find_group(menu_body: dict, name: str) -> dict:
    return next(group for group in menu_body["groups"] if group["name"] == name)


def _run_restaurant(client, dataset, spec) -> dict:
    """Drive one restaurant fully through the wizard. Returns a dict of observations."""
    obs: dict = {}

    created = client.post(
        "/api/onboarding", json={"locale": spec["locale"], "device": spec["device"]}
    )
    assert created.status_code == 200, created.text
    onboarding_id = created.json()["id"]
    obs["id"] = onboarding_id

    # ---- Legal ----
    dataset.legal = spec["legal"]
    legal = client.post(
        f"/api/onboarding/{onboarding_id}/legal/parse", files={"files": _pdf("kbis.pdf")}
    )
    assert legal.status_code == 200, legal.text
    legal_body = legal.json()
    assert legal_body["status"] == "ready"
    assert legal_body["fields"]["siren"]["value"] == spec["legal"]["siren"]
    # Validator must flag the real SIREN as valid.
    assert legal_body["fields"]["siren"]["valid"] is True
    assert legal_body["registry"]["status"] == "match"
    obs["legal_parse"] = legal_body

    # Edit a legal field via PUT (simulate a correction). Must persist.
    edited_legal = dict(legal_body)
    edited_legal["fields"] = dict(legal_body["fields"])
    rep = dict(edited_legal["fields"]["legal_representative"])
    rep["value"] = "CORRECTED REP"
    rep["provenance"] = "user_edited"
    rep["status"] = "present"
    edited_legal["fields"]["legal_representative"] = rep
    put_legal = client.put(
        f"/api/onboarding/{onboarding_id}/legal", json=edited_legal
    )
    assert put_legal.status_code == 200, put_legal.text
    assert put_legal.json()["fields"]["legal_representative"]["value"] == "CORRECTED REP"

    _confirm(client, onboarding_id, 1)

    # ---- Banking ----
    dataset.banking = spec["banking"]
    banking = client.post(
        f"/api/onboarding/{onboarding_id}/banking/parse", files={"files": _pdf("rib.pdf")}
    )
    assert banking.status_code == 200, banking.text
    banking_body = banking.json()
    assert banking_body["status"] == "ready"
    assert banking_body["fields"]["iban"]["value"] == spec["banking"]["iban"]
    assert banking_body["fields"]["iban"]["valid"] is True
    assert banking_body["fields"]["bic"]["valid"] is True
    assert banking_body["cross_doc_holder_match"] is True
    obs["banking_parse"] = banking_body

    _confirm(client, onboarding_id, 2)

    # ---- Menu ----
    dataset.menu = spec["menu"]
    menu = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse", files={"files": _image("menu.png")}
    )
    assert menu.status_code == 200, menu.text
    menu_body = menu.json()
    assert menu_body["status"] == "ready"
    obs["menu_parse"] = menu_body

    # No empty "Sans catégorie" bucket is added when everything is categorized.
    buckets = [group for group in menu_body["groups"] if group["name"] == "Sans catégorie"]
    assert all(bucket["items"] for bucket in buckets)

    # Source URL must be rewritten to the served path.
    source = menu_body["source_files"][0]
    assert source["url"] == f"/api/onboarding/{onboarding_id}/files/{source['id']}"

    spec["menu_assert"](menu_body)

    # ---- Menu edit via PUT: add a missing item to the first group, remove an item ----
    first_group = menu_body["groups"][0]
    added_item = {
        "id": "item_manual_added",
        "name": {
            "value": "Plat Ajouté Main",
            "status": "present",
            "confidence": None,
            "provenance": "user_added",
            "valid": None,
        },
        "description": {
            "value": None,
            "status": "missing",
            "confidence": None,
            "provenance": "user_added",
            "valid": None,
        },
        "prices": [{"label": None, "amount": "9,99"}],
        "confidence": None,
        "provenance": "user_added",
    }
    original_first_count = len(first_group["items"])
    edited_menu = dict(menu_body)
    edited_menu["groups"] = [dict(group) for group in menu_body["groups"]]
    edited_first = dict(edited_menu["groups"][0])
    edited_first["items"] = list(first_group["items"]) + [added_item]
    edited_menu["groups"][0] = edited_first

    # Remove an item: drop the last item of the second group if it has >1.
    removed_name = None
    if len(menu_body["groups"]) > 1 and len(menu_body["groups"][1]["items"]) >= 1:
        edited_second = dict(edited_menu["groups"][1])
        removed_name = edited_second["items"][-1]["name"]["value"]
        edited_second["items"] = edited_second["items"][:-1]
        edited_menu["groups"][1] = edited_second

    put_menu = client.put(f"/api/onboarding/{onboarding_id}/menu", json=edited_menu)
    assert put_menu.status_code == 200, put_menu.text
    put_menu_body = put_menu.json()
    new_first = put_menu_body["groups"][0]
    assert len(new_first["items"]) == original_first_count + 1
    assert any(item["name"]["value"] == "Plat Ajouté Main" for item in new_first["items"])
    assert any(item["provenance"] == "user_added" for item in new_first["items"])
    if removed_name is not None:
        second_names = [
            item["name"]["value"] for item in put_menu_body["groups"][1]["items"]
        ]
        assert removed_name not in second_names

    _confirm(client, onboarding_id, 3)

    # ---- Final reads ----
    final = client.get(f"/api/onboarding/{onboarding_id}")
    assert final.status_code == 200, final.text
    final_body = final.json()
    assert final_body["step"] == 4
    assert final_body["confirmed"] == {"legal": True, "banking": True, "menu": True}
    # Legal edit survived all the way to the final state.
    assert (
        final_body["legal"]["fields"]["legal_representative"]["value"] == "CORRECTED REP"
    )
    # Menu add survived to the final state.
    assert any(
        item["name"]["value"] == "Plat Ajouté Main"
        for item in final_body["menu"]["groups"][0]["items"]
    )

    restaurant = client.get(f"/api/onboarding/{onboarding_id}/restaurant")
    assert restaurant.status_code == 200, restaurant.text
    assert restaurant.json()["id"] == onboarding_id
    assert restaurant.json()["step"] == 4

    obs["final"] = final_body
    obs["device"] = spec["device"]
    return obs


def _assert_koyuki(menu_body: dict) -> None:
    pizzas = _find_group(menu_body, "PIZZAS")
    assert len(pizzas["items"]) == 3
    # Variant prices on the Tacos item preserved as labelled strings.
    tacos = _find_group(menu_body, "TACOS")
    tacos_item = tacos["items"][0]
    assert len(tacos_item["prices"]) == 2
    amounts = {variant["amount"] for variant in tacos_item["prices"]}
    assert amounts == {"9,00", "7,00"}
    for variant in tacos_item["prices"]:
        assert isinstance(variant["amount"], str)
    # European decimal kept verbatim.
    kebab = _find_group(menu_body, "KEBAB")
    assert kebab["items"][0]["prices"][0]["amount"] == "8,50"
    assert isinstance(kebab["items"][0]["prices"][0]["amount"], str)


def _assert_drinks(menu_body: dict) -> None:
    bieres = _find_group(menu_body, "BIERES")
    pression = bieres["items"][0]
    # Two size variants 25cl/50cl preserved with labels, amounts as strings.
    assert len(pression["prices"]) == 2
    labels = [variant["label"] for variant in pression["prices"]]
    assert labels == ["25 cl", "50 cl"]
    for variant in pression["prices"]:
        assert isinstance(variant["amount"], str)
    assert pression["prices"][0]["amount"] == "3,50"
    # The low-confidence Chablis (0.5) is flagged low_confidence, not dropped.
    vins = _find_group(menu_body, "VINS")
    chablis = next(item for item in vins["items"] if item["name"]["value"] == "Chablis")
    assert chablis["name"]["status"] == "low_confidence"


def _assert_priceless(menu_body: dict) -> None:
    sauces = _find_group(menu_body, "SAUCES")
    assert len(sauces["items"]) == 3
    # Price-less items: empty prices list, never floats, never crash.
    for item in sauces["items"]:
        assert item["prices"] == []
    plats = _find_group(menu_body, "PLATS")
    assert plats["items"][0]["prices"][0]["amount"] == "14,00"
    assert isinstance(plats["items"][0]["prices"][0]["amount"], str)


def test_multi_onboarding_full_flow_and_admin_aggregates(client, dataset):
    specs = [
        {
            "name": "koyuki",
            "device": "mobile",
            "locale": "fr",
            "legal": KOYUKI_LEGAL,
            "banking": KOYUKI_BANKING,
            "menu": KOYUKI_MENU,
            "menu_assert": _assert_koyuki,
        },
        {
            "name": "drinks",
            "device": "desktop",
            "locale": "fr",
            "legal": DRINKS_LEGAL,
            "banking": DRINKS_BANKING,
            "menu": DRINKS_MENU,
            "menu_assert": _assert_drinks,
        },
        {
            "name": "priceless",
            "device": "mobile",
            "locale": "en",
            "legal": PRICELESS_LEGAL,
            "banking": PRICELESS_BANKING,
            "menu": PRICELESS_MENU,
            "menu_assert": _assert_priceless,
        },
    ]

    observations = [_run_restaurant(client, dataset, spec) for spec in specs]
    assert len({obs["id"] for obs in observations}) == 3

    # ---- Admin onboardings list aggregates all three ----
    rows = client.get("/api/admin/onboardings")
    assert rows.status_code == 200, rows.text
    rows_body = rows.json()
    by_id = {row["id"]: row for row in rows_body}
    for obs in observations:
        assert obs["id"] in by_id
        row = by_id[obs["id"]]
        # All three are completed (step 4) with all blocks confirmed, valid SIREN+IBAN,
        # and menu items -> publishable.
        assert row["status"] == "publishable", row
        assert row["step"] == 4
        assert row["ai_cost_eur"] > 0
        assert row["registry_status"] == "match"

    # ---- Admin metrics aggregate the funnel/cost/device split correctly ----
    metrics = client.get("/api/admin/metrics")
    assert metrics.status_code == 200, metrics.text
    body = metrics.json()
    assert {"funnel", "ai_cost", "quality", "friction"} <= set(body.keys())

    funnel = {stage["step"]: stage for stage in body["funnel"]}
    # Device split: 2 mobile (koyuki, priceless) + 1 desktop (drinks).
    assert funnel["started"]["mobile"] == 2
    assert funnel["started"]["desktop"] == 1
    # Every stage carried through to publishable for all three.
    for stage in ("started", "legal_done", "banking_done", "menu_done", "publishable"):
        assert funnel[stage]["mobile"] == 2
        assert funnel[stage]["desktop"] == 1

    # AI cost aggregates across onboardings. Each restaurant ran 3 parses at 0.02 EUR = 0.06,
    # three restaurants -> 0.18 total, spread over both models (legal/banking sonnet, menu opus).
    by_model = body["ai_cost"]["by_model"]
    by_step = body["ai_cost"]["by_step"]
    total_model = round(sum(by_model.values()), 6)
    total_step = round(sum(by_step.values()), 6)
    assert total_model == pytest.approx(0.18, abs=1e-6)
    assert total_step == pytest.approx(0.18, abs=1e-6)
    assert set(by_step.keys()) == {"legal", "banking", "menu"}
    # per_publishable = total / 3 publishable.
    assert body["ai_cost"]["per_publishable_eur"] == pytest.approx(0.06, abs=1e-6)


def test_corrupted_iban_is_flagged_invalid(client, dataset):
    """A deliberately corrupted IBAN must come back valid=False from the parse path."""
    dataset.legal = KOYUKI_LEGAL
    created = client.post("/api/onboarding", json={"device": "desktop"})
    onboarding_id = created.json()["id"]
    client.post(
        f"/api/onboarding/{onboarding_id}/legal/parse", files={"files": _pdf("kbis.pdf")}
    )

    corrupted = dict(KOYUKI_BANKING)
    # Flip the final check digit so mod-97 fails.
    corrupted["iban"] = "FR7618306000457021845630175"
    dataset.banking = corrupted
    banking = client.post(
        f"/api/onboarding/{onboarding_id}/banking/parse", files={"files": _pdf("rib.pdf")}
    )
    assert banking.status_code == 200, banking.text
    body = banking.json()
    # Still "ready" (holder + iban present) but the checksum flags it invalid.
    assert body["status"] == "ready"
    assert body["fields"]["iban"]["value"] == "FR7618306000457021845630175"
    assert body["fields"]["iban"]["valid"] is False


def test_couldnt_parse_block_when_extractor_returns_nothing(client, dataset):
    """When the extractor yields no data, the block degrades to couldnt_parse, not 500."""
    dataset.legal = None  # extractor returns couldnt_parse
    created = client.post("/api/onboarding", json={})
    onboarding_id = created.json()["id"]
    legal = client.post(
        f"/api/onboarding/{onboarding_id}/legal/parse", files={"files": _pdf("kbis.pdf")}
    )
    assert legal.status_code == 200, legal.text
    body = legal.json()
    assert body["status"] == "couldnt_parse"
    for field in body["fields"].values():
        assert field["value"] is None
        assert field["status"] == "missing"


def test_priceless_reparse_preserves_user_added_and_bucket(client, dataset):
    """A user-added 'Sans catégorie' section survives a re-parse and is never duplicated."""
    created = client.post("/api/onboarding", json={"device": "mobile"})
    onboarding_id = created.json()["id"]

    dataset.menu = PRICELESS_MENU
    first = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse", files={"files": _image("a.png")}
    ).json()
    # No empty bucket is auto-created; the user adds one on demand when they need it.
    assert [group for group in first["groups"] if group["name"] == "Sans catégorie"] == []

    edited = dict(first)
    edited["groups"] = [dict(group) for group in first["groups"]]
    edited["groups"].append(
        {
            "id": "group_uncategorized",
            "name": "Sans catégorie",
            "items": [
                {
                    "id": "item_in_bucket",
                    "name": {"value": "Item Maison", "status": "present", "confidence": None,
                             "provenance": "user_added", "valid": None},
                    "description": {"value": None, "status": "missing", "confidence": None,
                                    "provenance": "user_added", "valid": None},
                    "prices": [],
                    "confidence": None,
                    "provenance": "user_added",
                }
            ],
            "provenance": "user_added",
            "source_file_ids": [],
        }
    )
    client.put(f"/api/onboarding/{onboarding_id}/menu", json=edited)

    # Re-parse the same menu. The user-added bucket + item must survive, no duplicate bucket,
    # and PLATS must not gain duplicate items.
    second = client.post(
        f"/api/onboarding/{onboarding_id}/menu/parse", files={"files": _image("b.png")}
    ).json()
    bucket_groups = [group for group in second["groups"] if group["name"] == "Sans catégorie"]
    assert len(bucket_groups) == 1
    assert any(item["name"]["value"] == "Item Maison" for item in bucket_groups[0]["items"])
    plats = _find_group(second, "PLATS")
    # Original PLATS had exactly 1 item; re-parse must not duplicate it.
    assert len(plats["items"]) == 1
