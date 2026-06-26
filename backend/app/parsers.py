import uuid

from pydantic import BaseModel, Field

from app.config import settings
from app.ingest import IngestedFile
from app.llm import ContentBlock, ParseResult, ParseUsage, extract
from app.schemas import (
    BankingBlock,
    BankingFields,
    Field_,
    LegalBlock,
    LegalFields,
    MenuBlock,
    MenuGroup,
    MenuItem,
    PriceVariant,
)

LOW_CONFIDENCE_THRESHOLD = 0.6
UNCATEGORIZED_GROUP_NAME = "Sans catégorie"

LEGAL_INSTRUCTION = (
    "This is a French company registration document (Kbis or SIRENE/Avis de situation). "
    "Extract the legal entity fields. Keep the original language and spelling. "
    "For legal_form, return the short acronym (for example 'SAS', 'SARL', 'SA', 'EURL') derived "
    "from the full legal form text. The SIREN is 9 digits; the SIRET is 14 digits. "
    "If a field is not printed on the document, leave its value null. "
    "Give a confidence between 0 and 1 for every field reflecting how clearly it is printed."
)

BANKING_INSTRUCTION = (
    "This is a French bank account details document (RIB - Relevé d'Identité Bancaire). "
    "Extract the account holder, bank name, IBAN and BIC/SWIFT. "
    "Keep the IBAN and BIC exactly as printed (uppercase, you may drop spaces in the IBAN). "
    "If a field is not present, leave its value null. "
    "Give a confidence between 0 and 1 for every field."
)

MENU_INSTRUCTION = (
    "This is a restaurant menu (a photo, screenshot or PDF page). "
    "Read it carefully and return the dishes grouped into the sections shown in the layout. "
    "Read multi-column layouts in reading order. Ignore phone UI chrome such as the iOS status "
    "bar, battery, time, browser address bar and on-screen buttons in screenshots. "
    "Keep all content in its original language. "
    "Prices MUST stay as the original strings (for example '12,50', '3 €', '10.00€'); never "
    "convert them to numbers. An item can have several prices (variants like '25 cl' / '50 cl' "
    "or 'Verre' / 'Bouteille'); put each in the prices list with its label. An item with no "
    "price is valid: return an empty prices list. "
    "Use the section title from the menu as the group name; if a dish has no section, use "
    f"'{UNCATEGORIZED_GROUP_NAME}'. Give a confidence between 0 and 1 for each item."
)


class _LegalExtraction(BaseModel):
    legal_name: str | None = None
    legal_name_confidence: float | None = None
    siren: str | None = None
    siren_confidence: float | None = None
    siret: str | None = None
    siret_confidence: float | None = None
    legal_form: str | None = None
    legal_form_confidence: float | None = None
    registered_address: str | None = None
    registered_address_confidence: float | None = None
    legal_representative: str | None = None
    legal_representative_confidence: float | None = None


class _BankingExtraction(BaseModel):
    account_holder: str | None = None
    account_holder_confidence: float | None = None
    bank_name: str | None = None
    bank_name_confidence: float | None = None
    iban: str | None = None
    iban_confidence: float | None = None
    bic: str | None = None
    bic_confidence: float | None = None


class _PriceVariant(BaseModel):
    label: str | None = None
    amount: str | None = None


class _MenuItem(BaseModel):
    name: str | None = None
    description: str | None = None
    prices: list[_PriceVariant] = Field(default_factory=list)
    confidence: float | None = None


class _MenuGroup(BaseModel):
    name: str
    items: list[_MenuItem] = Field(default_factory=list)


class _MenuExtraction(BaseModel):
    groups: list[_MenuGroup] = Field(default_factory=list)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _field_from_value(value: str | None, confidence: float | None) -> Field_:
    cleaned = value.strip() if isinstance(value, str) else value
    if not cleaned:
        return Field_(value=None, status="missing", confidence=None, provenance="parser")
    status = "low_confidence" if (confidence or 0.0) < LOW_CONFIDENCE_THRESHOLD else "present"
    return Field_(value=cleaned, status=status, confidence=confidence, provenance="parser")


def _strip_spaces(value: str | None) -> str | None:
    if not isinstance(value, str):
        return value
    return "".join(value.split()).upper() or None


class LegalParseOutput(BaseModel):
    block: LegalBlock
    usage: ParseUsage


class BankingParseOutput(BaseModel):
    block: BankingBlock
    usage: ParseUsage


class MenuFileParseOutput(BaseModel):
    groups: list[MenuGroup]
    status: str
    usage: ParseUsage


def parse_legal(blocks: list[ContentBlock]) -> LegalParseOutput:
    result = extract(
        model=settings.model_legal,
        output_model=_LegalExtraction,
        blocks=blocks,
        instruction=LEGAL_INSTRUCTION,
        max_tokens=4096,
    )
    return LegalParseOutput(block=_build_legal_block(result), usage=result.usage)


def _build_legal_block(result: ParseResult) -> LegalBlock:
    if result.status != "ok" or result.data is None:
        return LegalBlock(status="couldnt_parse", fields=LegalFields())

    data = _LegalExtraction.model_validate(result.data)
    fields = LegalFields(
        legal_name=_field_from_value(data.legal_name, data.legal_name_confidence),
        siren=_field_from_value(_strip_spaces(data.siren), data.siren_confidence),
        siret=_field_from_value(_strip_spaces(data.siret), data.siret_confidence),
        legal_form=_field_from_value(data.legal_form, data.legal_form_confidence),
        registered_address=_field_from_value(
            data.registered_address, data.registered_address_confidence
        ),
        legal_representative=_field_from_value(
            data.legal_representative, data.legal_representative_confidence
        ),
    )
    has_minimum = bool(fields.legal_name.value) and bool(fields.siren.value)
    status = "ready" if has_minimum else "couldnt_parse"
    return LegalBlock(status=status, fields=fields)


def parse_banking(blocks: list[ContentBlock]) -> BankingParseOutput:
    result = extract(
        model=settings.model_banking,
        output_model=_BankingExtraction,
        blocks=blocks,
        instruction=BANKING_INSTRUCTION,
        max_tokens=4096,
    )
    return BankingParseOutput(block=_build_banking_block(result), usage=result.usage)


def _build_banking_block(result: ParseResult) -> BankingBlock:
    if result.status != "ok" or result.data is None:
        return BankingBlock(status="couldnt_parse", fields=BankingFields())

    data = _BankingExtraction.model_validate(result.data)
    fields = BankingFields(
        account_holder=_field_from_value(data.account_holder, data.account_holder_confidence),
        bank_name=_field_from_value(data.bank_name, data.bank_name_confidence),
        iban=_field_from_value(_strip_spaces(data.iban), data.iban_confidence),
        bic=_field_from_value(_strip_spaces(data.bic), data.bic_confidence),
    )
    has_minimum = bool(fields.account_holder.value) and bool(fields.iban.value)
    status = "ready" if has_minimum else "couldnt_parse"
    return BankingBlock(status=status, fields=fields)


def parse_menu_file(ingested: IngestedFile) -> MenuFileParseOutput:
    result = extract(
        model=settings.model_menu,
        output_model=_MenuExtraction,
        blocks=[ingested.block],
        instruction=MENU_INSTRUCTION,
        max_tokens=8000,
    )
    if result.status != "ok" or result.data is None:
        return MenuFileParseOutput(groups=[], status="couldnt_parse", usage=result.usage)

    extraction = _MenuExtraction.model_validate(result.data)
    groups = _build_menu_groups(extraction, ingested.file_id)
    has_usable = any(group.items for group in groups)
    status = "ready" if has_usable else "couldnt_parse"
    return MenuFileParseOutput(groups=groups, status=status, usage=result.usage)


def _build_menu_groups(extraction: _MenuExtraction, file_id: str) -> list[MenuGroup]:
    groups: list[MenuGroup] = []
    for raw_group in extraction.groups:
        items: list[MenuItem] = []
        for raw_item in raw_group.items:
            name_value = raw_item.name.strip() if raw_item.name else None
            if not name_value:
                continue
            name_status = (
                "low_confidence"
                if (raw_item.confidence or 0.0) < LOW_CONFIDENCE_THRESHOLD
                else "present"
            )
            items.append(
                MenuItem(
                    id=_new_id("item"),
                    name=Field_(
                        value=name_value,
                        status=name_status,
                        confidence=raw_item.confidence,
                        provenance="parser",
                    ),
                    description=_field_from_value(raw_item.description, raw_item.confidence),
                    prices=[
                        PriceVariant(label=variant.label, amount=variant.amount)
                        for variant in raw_item.prices
                    ],
                    confidence=raw_item.confidence,
                    provenance="parser",
                )
            )
        if not items:
            continue
        groups.append(
            MenuGroup(
                id=_new_id("group"),
                name=raw_group.name.strip() or UNCATEGORIZED_GROUP_NAME,
                items=items,
                provenance="parser",
                source_file_ids=[file_id],
            )
        )
    return groups


def empty_menu_block() -> MenuBlock:
    return MenuBlock(status="empty", groups=[], source_files=[])
