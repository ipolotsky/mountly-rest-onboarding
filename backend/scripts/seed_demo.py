"""Populate the database with realistic, varied demo onboardings and analytics events so
the admin dashboard ( /admin ) shows meaningful charts.

Run from the backend root:

    python -m scripts.seed_demo --reset

`--reset` wipes existing onboardings, events and stored-file rows first.

The target ("activated") action modelled here is the customer clicking "Looks good" on the
menu review, which confirms the menu and emits onboarding_completed. Publishing is a
separate convenience step, so `published` is set on only a minority of activated
onboardings and never drives the funnel, the status or the time-to-value.
"""

import argparse
import random
import uuid
from datetime import UTC, datetime, timedelta

from app.database import SessionLocal, create_tables
from app.models import Event, Onboarding, StoredFile
from app.schemas import (
    BankingBlock,
    BankingFields,
    Confirmed,
    Field_,
    LegalBlock,
    LegalFields,
    LegalRegistry,
    MenuBlock,
    MenuGroup,
    MenuItem,
    PriceVariant,
)
from app.validators import validate_iban, validate_siren, validate_siret

NAME_PATTERNS = [
    "Le {noun}",
    "La {noun}",
    "Chez {first}",
    "Bistrot {noun}",
    "Brasserie {noun}",
    "Auberge {noun}",
    "Le Comptoir {noun}",
    "Maison {last}",
    "Les {noun}",
]
NAME_NOUNS = [
    "Gourmet",
    "Jardin",
    "Marché",
    "Tournesol",
    "Soleil Levant",
    "Vieux Four",
    "Régal",
    "Festin",
    "Potager",
    "Olivier",
    "Cèdre",
    "Lavandin",
    "Quai",
    "Refuge",
    "Ardoise",
    "Trois Cloches",
    "Bon Coin",
    "Saveurs",
    "Petit Gourmet",
    "Table Ronde",
]
FIRST_NAMES = [
    "Margot",
    "Olivier",
    "Léa",
    "Hugo",
    "Camille",
    "Paul",
    "Anna",
    "Lucie",
    "Marc",
    "Émile",
    "Sophie",
    "Théo",
    "Clara",
    "Antoine",
    "Inès",
]
LAST_NAMES = [
    "Bernard",
    "Dubois",
    "Martin",
    "Garnier",
    "Rey",
    "Weber",
    "Morand",
    "Faure",
    "Henry",
    "Lefevre",
    "Roux",
    "Blanc",
    "Girard",
    "Mercier",
    "Colin",
]
STREETS = [
    "Rue des Lilas",
    "Place du Marché",
    "Avenue Jean Jaurès",
    "Rue Saint-Michel",
    "Boulevard Victor Hugo",
    "Rue des Tilleuls",
    "Route du Palais",
    "Cours Lafayette",
    "Place de l'Église",
    "Rue Nationale",
    "Rue Pasteur",
    "Allée des Roses",
    "Quai de Seine",
    "Chemin des Vignes",
]
CITIES = [
    "75011 Paris",
    "69001 Lyon",
    "31000 Toulouse",
    "33000 Bordeaux",
    "06000 Nice",
    "67000 Strasbourg",
    "74110 Morzine",
    "21000 Dijon",
    "59000 Lille",
    "44000 Nantes",
    "35000 Rennes",
    "13001 Marseille",
    "34000 Montpellier",
]
BANKS = [
    "Crédit Agricole",
    "BNP Paribas",
    "Société Générale",
    "Banque Populaire",
    "LCL",
    "Caisse d'Épargne",
    "CIC",
    "La Banque Postale",
]
LEGAL_FORMS = ["SAS", "SARL", "EURL", "SASU", "SA"]

DISH_POOL = {
    "Entrées": [
        ("Soupe à l'oignon", "Gratinée au comté", 7, 10),
        ("Salade de chèvre chaud", "Miel et noix", 9, 13),
        ("Œuf parfait", "Crème de champignons", 9, 12),
        ("Velouté de potiron", "Huile de noisette", 7, 9),
        ("Terrine maison", "Cornichons et pain grillé", 8, 11),
        ("Burrata", "Tomates anciennes, basilic", 11, 15),
    ],
    "Plats": [
        ("Magret de canard", "Sauce au miel", 19, 26),
        ("Risotto aux cèpes", "Parmesan affiné", 16, 22),
        ("Filet de bar", "Beurre blanc", 21, 28),
        ("Burger maison", "Frites fraîches", 14, 19),
        ("Bœuf bourguignon", "Purée maison", 17, 23),
        ("Suprême de volaille", "Jus corsé, légumes de saison", 16, 21),
        ("Gnocchis", "Sauce tomate basilic", 14, 18),
    ],
    "Desserts": [
        ("Tarte Tatin", "Glace vanille", 7, 10),
        ("Fondant au chocolat", "Cœur coulant", 7, 10),
        ("Crème brûlée", "Gousse de vanille", 6, 9),
        ("Profiteroles", "Sauce chocolat chaud", 8, 11),
        ("Tiramisu maison", "Café et cacao", 7, 9),
    ],
    "Boissons": [
        ("Verre de Côtes du Rhône", "13 cl", 5, 8),
        ("Limonade artisanale", "Citron de Menton", 4, 6),
        ("Café gourmand", "Mignardises maison", 7, 9),
        ("Eau minérale", "75 cl", 3, 5),
    ],
}

ERROR_TYPES = {
    1: ["siren_invalid", "legal_parse_failed", "registered_address_missing", "siret_mismatch"],
    2: ["iban_checksum_failed", "holder_mismatch", "banking_parse_failed", "bic_invalid"],
    3: ["menu_low_confidence", "duplicate_file", "menu_empty", "price_unreadable"],
}

# Activation funnel taper: current step reached (1..4). Step 4 means the customer clicked
# "Looks good" on the menu and landed on the restaurant page.
REACHED_PROFILE = [1] * 12 + [2] * 9 + [3] * 7 + [4] * 12


def _valid_siren(rng: random.Random) -> str:
    while True:
        digits = "".join(str(rng.randint(0, 9)) for _ in range(9))
        if validate_siren(digits):
            return digits


def _valid_siret(rng: random.Random) -> str:
    while True:
        digits = "".join(str(rng.randint(0, 9)) for _ in range(14))
        if validate_siret(digits):
            return digits


def _valid_fr_iban(rng: random.Random) -> str:
    while True:
        bban = "".join(str(rng.randint(0, 9)) for _ in range(23))
        numeric = "".join(str(int(character, 36)) for character in bban + "FR00")
        check = 98 - (int(numeric) % 97)
        iban = f"FR{check:02d}{bban}"
        if validate_iban(iban):
            return iban


def _restaurant(rng: random.Random) -> tuple[str, str, str]:
    pattern = rng.choice(NAME_PATTERNS)
    name = pattern.format(
        noun=rng.choice(NAME_NOUNS), first=rng.choice(FIRST_NAMES), last=rng.choice(LAST_NAMES)
    )
    address = f"{rng.randint(1, 120)} {rng.choice(STREETS)} {rng.choice(CITIES)}"
    representative = f"{rng.choice(LAST_NAMES)} {rng.choice(FIRST_NAMES)}"
    return name, address, representative


def _price(rng: random.Random, low: int, high: int) -> str:
    base = rng.randint(low, high)
    return f"{base},{rng.choice(['00', '50'])}"


def _field(
    value: str | None, status: str = "present", provenance: str = "parser", valid=None
) -> Field_:
    return Field_(value=value, status=status, confidence=0.95, provenance=provenance, valid=valid)


def _legal_block(
    rng: random.Random,
    name: str,
    address: str,
    representative: str,
    *,
    siren_valid: bool,
    low_confidence: bool,
    registry_status: str,
) -> LegalBlock:
    siren = _valid_siren(rng) if siren_valid else "000000000"
    addr_status = "low_confidence" if low_confidence else "present"
    return LegalBlock(
        status="ready",
        fields=LegalFields(
            legal_name=_field(name),
            siren=_field(siren, valid=siren_valid),
            siret=_field(_valid_siret(rng), valid=True),
            legal_form=_field(rng.choice(LEGAL_FORMS)),
            registered_address=_field(address, status=addr_status),
            legal_representative=_field(representative),
        ),
        registry=LegalRegistry(status=registry_status, name_match=registry_status == "match"),
    )


def _banking_block(rng: random.Random, holder: str, *, iban_valid: bool) -> BankingBlock:
    iban = _valid_fr_iban(rng) if iban_valid else "FR0000000000000000000000000"
    return BankingBlock(
        status="ready",
        fields=BankingFields(
            account_holder=_field(holder),
            bank_name=_field(rng.choice(BANKS)),
            iban=_field(iban, valid=iban_valid),
            bic=_field("AGRIFRPP878", valid=True),
        ),
        cross_doc_holder_match=True,
    )


def _menu_block(rng: random.Random, *, with_items: bool, low_confidence: bool) -> MenuBlock:
    if not with_items:
        return MenuBlock(status="ready", groups=[], source_files=[])
    categories = [c for c in DISH_POOL if rng.random() < 0.75] or ["Plats"]
    groups: list[MenuGroup] = []
    for category in categories:
        pool = DISH_POOL[category]
        chosen = rng.sample(pool, k=min(len(pool), rng.randint(2, 5)))
        items: list[MenuItem] = []
        for index, (dish, description, low, high) in enumerate(chosen):
            user_added = rng.random() < 0.15
            name_status = "low_confidence" if low_confidence and index == 0 else "present"
            items.append(
                MenuItem(
                    id=uuid.uuid4().hex[:8],
                    name=_field(
                        dish,
                        status=name_status,
                        provenance="user_added" if user_added else "parser",
                    ),
                    description=_field(description),
                    prices=[PriceVariant(label=None, amount=_price(rng, low, high))],
                    confidence=round(rng.uniform(0.7, 0.99), 2),
                    provenance="user_added" if user_added else "parser",
                )
            )
        groups.append(MenuGroup(id=uuid.uuid4().hex[:8], name=category, items=items))
    return MenuBlock(status="ready", groups=groups, source_files=[])


def _event(kind: str, onboarding_id: str, created_at: datetime, device: str, props: dict) -> Event:
    return Event(
        kind=kind,
        onboarding_id=onboarding_id,
        device=device,
        locale="fr",
        created_at=created_at,
        props=props,
    )


def _ttv_seconds(rng: random.Random) -> int:
    bucket = rng.choices(["lt2m", "2to5m", "5to10m", "gt10m"], weights=[3, 4, 2, 1])[0]
    ranges = {"lt2m": (45, 118), "2to5m": (125, 295), "5to10m": (310, 590), "gt10m": (620, 1500)}
    low, high = ranges[bucket]
    return rng.randint(low, high)


def _cost(rng: random.Random, doc_type: str) -> float:
    return round(rng.uniform(0.04, 0.12) if doc_type == "menu" else rng.uniform(0.01, 0.05), 6)


def seed(session, rng: random.Random) -> int:
    now = datetime.now(UTC)
    profiles = list(REACHED_PROFILE)
    rng.shuffle(profiles)
    doc_by_step = {1: "legal", 2: "banking", 3: "menu"}

    for reached in profiles:
        onboarding_id = uuid.uuid4().hex[:16]
        device = "mobile" if rng.random() < 0.55 else "desktop"
        created_at = now - timedelta(
            days=rng.randint(0, 13), hours=rng.randint(0, 23), minutes=rng.randint(0, 59)
        )
        name, address, representative = _restaurant(rng)
        low_confidence = rng.random() < 0.35
        registry_status = rng.choices(
            ["match", "no_match", "unavailable", "skipped"], weights=[6, 2, 1, 1]
        )[0]

        # A document the customer reaches can be parsed (incurring AI cost) before it is
        # confirmed; some bail after a parse without clicking "Looks good".
        confirmed_steps = list(range(1, reached))
        parsed_steps = list(confirmed_steps)
        if reached <= 3 and rng.random() < 0.7:
            parsed_steps.append(reached)

        # Activated (reached the restaurant page) onboardings are mostly valid; a few carry a
        # broken legal/banking field or an empty menu so "completed" shows up next to
        # "publishable" in the table.
        broken = rng.random() < 0.35 if reached >= 4 else False
        broken_kind = rng.choice(["siren", "iban", "menu"]) if broken else None
        siren_valid = broken_kind != "siren"
        iban_valid = broken_kind != "iban"
        menu_with_items = broken_kind != "menu"

        legal = (
            _legal_block(
                rng,
                name,
                address,
                representative,
                siren_valid=siren_valid,
                low_confidence=low_confidence,
                registry_status=registry_status,
            )
            if 1 in parsed_steps
            else LegalBlock()
        )
        banking = (
            _banking_block(rng, name, iban_valid=iban_valid)
            if 2 in parsed_steps
            else BankingBlock()
        )
        menu = (
            _menu_block(rng, with_items=menu_with_items, low_confidence=low_confidence)
            if 3 in parsed_steps
            else MenuBlock()
        )
        confirmed = Confirmed(legal=reached >= 2, banking=reached >= 3, menu=reached >= 4)

        activated = reached >= 4
        csat = None
        if activated and rng.random() < 0.7:
            csat = rng.choices([5, 4, 3, 2, 1], weights=[6, 5, 3, 2, 1])[0]
        # Publishing is optional convenience, decoupled from activation.
        published = activated and rng.random() < 0.4

        session.add(
            Onboarding(
                id=onboarding_id,
                created_at=created_at,
                updated_at=created_at + timedelta(minutes=rng.randint(2, 20)),
                locale="fr",
                device=device,
                step=reached,
                confirmed=confirmed.model_dump(),
                legal=legal.model_dump(),
                banking=banking.model_dump(),
                menu=menu.model_dump(),
                published=published,
                feedback_submitted=csat is not None,
                csat=csat,
                feedback_at=created_at + timedelta(minutes=25) if csat is not None else None,
            )
        )

        session.add(_event("onboarding_started", onboarding_id, created_at, device, {}))

        cursor = created_at + timedelta(seconds=rng.randint(5, 40))
        for step in confirmed_steps:
            dwell = rng.randint(25, 240)
            session.add(_event("step_viewed", onboarding_id, cursor, device, {"step": step}))
            session.add(
                _event(
                    "step_confirmed",
                    onboarding_id,
                    cursor + timedelta(seconds=dwell),
                    device,
                    {"step": step, "duration_ms": rng.randint(120, 400)},
                )
            )
            cursor = cursor + timedelta(seconds=dwell + rng.randint(5, 30))

        for step in parsed_steps:
            doc_type = doc_by_step[step]
            model = "claude-opus-4-8" if doc_type == "menu" else "claude-sonnet-4-6"
            session.add(
                _event(
                    "parse_completed",
                    onboarding_id,
                    created_at + timedelta(seconds=step * 30),
                    device,
                    {
                        "step": doc_type,
                        "doc_type": doc_type,
                        "model": model,
                        "tokens_in": rng.randint(800, 3000),
                        "tokens_out": rng.randint(300, 1200),
                        "latency_ms": rng.randint(1500, 6000),
                        "cost_eur": _cost(rng, doc_type),
                    },
                )
            )
            if doc_type == "legal":
                session.add(
                    _event(
                        "registry_verification_result",
                        onboarding_id,
                        created_at + timedelta(seconds=33),
                        device,
                        {
                            "identifier_type": "siren",
                            "lookup_status": registry_status,
                            "name_match": registry_status == "match",
                        },
                    )
                )

        # Errors: common where the customer stalled, occasional (recovered) where they advanced.
        if not activated and rng.random() < 0.7:
            for _ in range(rng.randint(1, 2)):
                error_step = reached
                session.add(
                    _event(
                        "error_shown",
                        onboarding_id,
                        cursor + timedelta(seconds=rng.randint(1, 40)),
                        device,
                        {"step": error_step, "error_type": rng.choice(ERROR_TYPES[error_step])},
                    )
                )
        elif confirmed_steps and rng.random() < 0.3:
            error_step = rng.choice(confirmed_steps)
            session.add(
                _event(
                    "error_shown",
                    onboarding_id,
                    created_at + timedelta(seconds=rng.randint(20, 120)),
                    device,
                    {"step": error_step, "error_type": rng.choice(ERROR_TYPES[error_step])},
                )
            )

        # "Looks good" on the menu completes the journey and anchors time-to-value.
        if activated:
            session.add(
                _event(
                    "onboarding_completed",
                    onboarding_id,
                    created_at + timedelta(seconds=_ttv_seconds(rng)),
                    device,
                    {},
                )
            )

    session.commit()
    return len(profiles)


def reset(session) -> None:
    session.query(Event).delete()
    session.query(StoredFile).delete()
    session.query(Onboarding).delete()
    session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo onboardings and analytics events.")
    parser.add_argument("--reset", action="store_true", help="Delete existing data first.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    args = parser.parse_args()

    create_tables()
    rng = random.Random(args.seed)
    with SessionLocal() as session:
        if args.reset:
            reset(session)
        count = seed(session, rng)
    print(f"Seeded {count} onboardings with analytics events.")


if __name__ == "__main__":
    main()
