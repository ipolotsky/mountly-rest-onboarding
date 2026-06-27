// Shared wire types. Mirror docs/API_CONTRACT.md exactly; do not introduce ad-hoc shapes.
// JSON is snake_case on the wire, so these keep snake_case too.

export type FieldStatus = "present" | "low_confidence" | "missing";
export type BlockStatus = "empty" | "parsing" | "ready" | "couldnt_parse";
export type Provenance = "parser" | "user_edited" | "user_added" | "user_confirmed";

export interface Field {
  value: string | null;
  status: FieldStatus;
  confidence: number | null;
  provenance: Provenance;
  valid: boolean | null;
}

export interface LegalFields {
  legal_name: Field;
  siren: Field;
  siret: Field;
  legal_form: Field;
  registered_address: Field;
  legal_representative: Field;
}

export type LegalFieldName = keyof LegalFields;

export interface RegistryInfo {
  status: "match" | "no_match" | "unavailable" | "skipped";
  name_match: boolean | null;
}

export interface LegalBlock {
  status: BlockStatus;
  fields: LegalFields;
  registry: RegistryInfo | null;
}

export interface BankingFields {
  account_holder: Field;
  bank_name: Field;
  iban: Field;
  bic: Field;
}

export type BankingFieldName = keyof BankingFields;

export interface BankingBlock {
  status: BlockStatus;
  fields: BankingFields;
  cross_doc_holder_match: boolean | null;
}

export interface PriceVariant {
  label: string | null;
  amount: string | null;
}

export interface MenuItem {
  id: string;
  name: Field;
  description: Field;
  prices: PriceVariant[];
  confidence: number | null;
  provenance: Provenance;
}

export interface MenuGroup {
  id: string;
  name: string;
  items: MenuItem[];
  provenance: Provenance;
  source_file_ids: string[];
}

export interface SourceFile {
  id: string;
  kind: "pdf" | "image";
  filename: string;
  url: string;
}

export interface MenuBlock {
  status: BlockStatus;
  groups: MenuGroup[];
  source_files: SourceFile[];
  skipped_duplicates?: string[];
}

export type Locale = "fr" | "en";
export type Device = "mobile" | "desktop";
export type Step = 1 | 2 | 3 | 4;

export interface ConfirmedFlags {
  legal: boolean;
  banking: boolean;
  menu: boolean;
}

export interface Onboarding {
  id: string;
  created_at: string;
  updated_at: string;
  locale: Locale;
  device: Device;
  step: Step;
  confirmed: ConfirmedFlags;
  published: boolean;
  feedback_submitted: boolean;
  csat: number | null;
  legal: LegalBlock;
  banking: BankingBlock;
  menu: MenuBlock;
}

export interface AnalyticsEvent {
  name: string;
  onboarding_id: string;
  session_id: string;
  device: Device;
  locale: Locale;
  schema_version: number;
  ts: string;
  props?: Record<string, unknown>;
}

export interface FeedbackPayload {
  csat: number;
  answers: Record<string, string>;
}

export interface AdminOnboardingRow {
  id: string;
  restaurant_name: string | null;
  status: string;
  device: Device;
  step: number;
  created_at: string;
  ttv_ms: number | null;
  ai_cost_eur: number;
  registry_status: string | null;
  csat: number | null;
}

export interface AdminFeedbackRow {
  id: string;
  csat: number | null;
  helped: string | null;
  improve: string | null;
  submitted_at: string;
  device: Device;
  status: string;
}

export interface FunnelEntry {
  step: string;
  mobile: number;
  desktop: number;
}

export interface AiCostMetrics {
  per_publishable_eur: number;
  by_model: Record<string, number>;
  by_step: Record<string, number>;
}

export interface QualityMetrics {
  auto_fill_acceptance: Record<"legal" | "banking" | "menu", number>;
  menu_hand_added_share: number;
  registry_success_rate: number;
  low_confidence_rate: number;
}

export interface FrictionEntry {
  step: string;
  drop_off: number;
  top_reason: string | null;
  median_ms: number | null;
}

export interface AdminMetrics {
  funnel: FunnelEntry[];
  ai_cost: AiCostMetrics;
  quality: QualityMetrics;
  friction: FrictionEntry[];
}
