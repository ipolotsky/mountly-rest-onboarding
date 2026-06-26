from app.parsers import _build_menu_groups, _MenuExtraction


def _extract(payload: dict) -> list:
    return _build_menu_groups(_MenuExtraction.model_validate(payload), "file_1")


def test_european_decimal_price_kept_as_string():
    groups = _extract(
        {"groups": [{"name": "PLATS", "items": [
            {
                "name": "Tartiflette",
                "prices": [{"label": None, "amount": "12,50"}],
                "confidence": 0.9,
            }
        ]}]}
    )
    item = groups[0].items[0]
    assert item.prices[0].amount == "12,50"
    assert isinstance(item.prices[0].amount, str)


def test_dual_price_variants_are_preserved():
    groups = _extract(
        {"groups": [{"name": "VINS", "items": [
            {"name": "Côtes du Rhône", "prices": [
                {"label": "Verre", "amount": "3 €"},
                {"label": "Bouteille", "amount": "18 €"}
            ], "confidence": 0.85}
        ]}]}
    )
    prices = groups[0].items[0].prices
    assert len(prices) == 2
    assert prices[0].label == "Verre"
    assert prices[0].amount == "3 €"
    assert prices[1].label == "Bouteille"
    assert prices[1].amount == "18 €"


def test_priceless_item_is_valid_and_does_not_crash():
    groups = _extract(
        {"groups": [{"name": "SAUCES", "items": [
            {"name": "Blanche", "prices": [], "confidence": 0.8},
            {"name": "Harissa", "prices": [], "confidence": 0.8}
        ]}]}
    )
    items = groups[0].items
    assert len(items) == 2
    assert items[0].prices == []
    assert items[1].prices == []


def test_null_amount_variant_is_kept():
    groups = _extract(
        {"groups": [{"name": "DESSERTS", "items": [
            {
                "name": "Café gourmand",
                "prices": [{"label": "selon saison", "amount": None}],
                "confidence": 0.7,
            }
        ]}]}
    )
    variant = groups[0].items[0].prices[0]
    assert variant.amount is None
    assert variant.label == "selon saison"


def test_item_without_name_is_dropped():
    groups = _extract(
        {"groups": [{"name": "PLATS", "items": [
            {"name": None, "prices": [{"label": None, "amount": "5,00"}], "confidence": 0.9},
            {"name": "Frites", "prices": [{"label": None, "amount": "4,00"}], "confidence": 0.9}
        ]}]}
    )
    assert len(groups[0].items) == 1
    assert groups[0].items[0].name.value == "Frites"


def test_golden_menu_has_expected_pizza_count(menu_extraction):
    groups = _extract(menu_extraction)
    assert len(groups) >= 4
    pizzas = next(group for group in groups if group.name == "PIZZAS")
    assert len(pizzas.items) == 13
    sauces = next(group for group in groups if group.name == "SAUCES")
    assert all(item.prices == [] for item in sauces.items)
