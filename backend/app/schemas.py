from typing import Literal

from pydantic import BaseModel, Field

FieldStatus = Literal["present", "low_confidence", "missing"]
BlockStatus = Literal["empty", "parsing", "ready", "couldnt_parse"]
Provenance = Literal["parser", "user_edited", "user_added", "user_confirmed"]
Locale = Literal["fr", "en"]
Device = Literal["mobile", "desktop"]
Step = Literal[1, 2, 3, 4]


class Field_(BaseModel):
    value: str | None = None
    status: FieldStatus = "missing"
    confidence: float | None = None
    provenance: Provenance = "parser"
    valid: bool | None = None


class LegalRegistry(BaseModel):
    status: Literal["match", "no_match", "unavailable", "skipped"]
    name_match: bool | None = None


class LegalFields(BaseModel):
    legal_name: Field_ = Field(default_factory=Field_)
    siren: Field_ = Field(default_factory=Field_)
    siret: Field_ = Field(default_factory=Field_)
    legal_form: Field_ = Field(default_factory=Field_)
    registered_address: Field_ = Field(default_factory=Field_)
    legal_representative: Field_ = Field(default_factory=Field_)


class LegalBlock(BaseModel):
    status: BlockStatus = "empty"
    fields: LegalFields = Field(default_factory=LegalFields)
    registry: LegalRegistry | None = None


class BankingFields(BaseModel):
    account_holder: Field_ = Field(default_factory=Field_)
    bank_name: Field_ = Field(default_factory=Field_)
    iban: Field_ = Field(default_factory=Field_)
    bic: Field_ = Field(default_factory=Field_)


class BankingBlock(BaseModel):
    status: BlockStatus = "empty"
    fields: BankingFields = Field(default_factory=BankingFields)
    cross_doc_holder_match: bool | None = None


class PriceVariant(BaseModel):
    label: str | None = None
    amount: str | None = None


class MenuItem(BaseModel):
    id: str
    name: Field_ = Field(default_factory=Field_)
    description: Field_ = Field(default_factory=Field_)
    prices: list[PriceVariant] = Field(default_factory=list)
    confidence: float | None = None
    provenance: Provenance = "parser"


class MenuGroup(BaseModel):
    id: str
    name: str
    items: list[MenuItem] = Field(default_factory=list)
    provenance: Provenance = "parser"
    source_file_ids: list[str] = Field(default_factory=list)


class SourceFile(BaseModel):
    id: str
    kind: Literal["pdf", "image"]
    filename: str
    url: str


class MenuBlock(BaseModel):
    status: BlockStatus = "empty"
    groups: list[MenuGroup] = Field(default_factory=list)
    source_files: list[SourceFile] = Field(default_factory=list)


class Confirmed(BaseModel):
    legal: bool = False
    banking: bool = False
    menu: bool = False


class Onboarding(BaseModel):
    id: str
    created_at: str
    updated_at: str
    locale: Locale = "fr"
    device: Device = "desktop"
    step: Step = 1
    confirmed: Confirmed = Field(default_factory=Confirmed)
    legal: LegalBlock = Field(default_factory=LegalBlock)
    banking: BankingBlock = Field(default_factory=BankingBlock)
    menu: MenuBlock = Field(default_factory=MenuBlock)


class CreateOnboardingRequest(BaseModel):
    locale: Locale | None = None
    device: Device | None = None


class CreateOnboardingResponse(BaseModel):
    id: str


class ConfirmRequest(BaseModel):
    step: Step


class FeedbackRequest(BaseModel):
    csat: int = Field(ge=1, le=5)
    answers: dict[str, object] = Field(default_factory=dict)


class OkResponse(BaseModel):
    ok: bool = True


class AnalyticsEvent(BaseModel):
    name: str
    onboarding_id: str
    session_id: str
    device: Device
    locale: Locale
    schema_version: int
    ts: str
    props: dict[str, object] | None = None


class EventsRequest(BaseModel):
    events: list[AnalyticsEvent]


class AdminOnboardingRow(BaseModel):
    id: str
    status: str
    device: Device
    step: int
    created_at: str
    ttv_ms: int | None = None
    ai_cost_eur: float
    registry_status: str | None = None
    csat: int | None = None


class FunnelStage(BaseModel):
    step: str
    mobile: int
    desktop: int


class AdminCost(BaseModel):
    per_publishable_eur: float
    by_model: dict[str, float]
    by_step: dict[str, float]


class AdminQuality(BaseModel):
    auto_fill_acceptance: dict[str, float]
    menu_hand_added_share: float
    registry_success_rate: float
    low_confidence_rate: float


class FrictionStage(BaseModel):
    step: str
    drop_off: float
    top_reason: str | None = None
    median_ms: float | None = None


class AdminMetrics(BaseModel):
    funnel: list[FunnelStage]
    ai_cost: AdminCost
    quality: AdminQuality
    friction: list[FrictionStage]
