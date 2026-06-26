# API contract

This is the **single source of truth** shared by `backend/` (Pydantic) and `frontend/` (TS types).
Change it here first, then both sides. JSON is `snake_case` on the wire. All routes are under `/api`.

## Shared types

```ts
type FieldStatus = "present" | "low_confidence" | "missing";
type BlockStatus = "empty" | "parsing" | "ready" | "couldnt_parse";
type Provenance  = "parser" | "user_edited" | "user_added" | "user_confirmed";

// A single parsed/edited value. `value` is null when missing → render a placeholder, never blank.
interface Field {
  value: string | null;
  status: FieldStatus;
  confidence: number | null;     // 0..1, parser confidence; null for user-entered
  provenance: Provenance;
  valid: boolean | null;         // checksum/format result where applicable (SIREN/IBAN/BIC); else null
}

interface LegalBlock {
  status: BlockStatus;
  fields: {
    legal_name: Field;
    siren: Field;
    siret: Field;
    legal_form: Field;
    registered_address: Field;
    legal_representative: Field;
  };
  registry: {                    // non-blocking enrichment; null until attempted
    status: "match" | "no_match" | "unavailable" | "skipped";
    name_match: boolean | null;
  } | null;
}

interface BankingBlock {
  status: BlockStatus;
  fields: {
    account_holder: Field;
    bank_name: Field;
    iban: Field;
    bic: Field;
  };
  cross_doc_holder_match: boolean | null;   // RIB holder vs Kbis legal name
}

interface PriceVariant {
  label: string | null;          // e.g. "25 cl", "Bouteille"; null for a single unlabeled price
  amount: string | null;         // ORIGINAL string, e.g. "12,50" or "3 €"; null = no price (valid!)
}

interface MenuItem {
  id: string;
  name: Field;
  description: Field;
  prices: PriceVariant[];        // empty array = price-less item (valid)
  confidence: number | null;
  provenance: Provenance;
}

interface MenuGroup {
  id: string;
  name: string;                  // "Sans catégorie" is the special, undeletable bucket
  items: MenuItem[];
  provenance: Provenance;
  source_file_ids: string[];
}

interface SourceFile {
  id: string;
  kind: "pdf" | "image";
  filename: string;
  url: string;                   // for the source-preview pane (served by the app)
}

interface MenuBlock {
  status: BlockStatus;
  groups: MenuGroup[];
  source_files: SourceFile[];
  skipped_duplicates?: string[];   // only on POST /menu/parse responses: filenames identical (by
                                   // content hash) to an already-uploaded file and therefore skipped
}

interface Onboarding {
  id: string;
  created_at: string;            // ISO 8601
  updated_at: string;
  locale: "fr" | "en";
  device: "mobile" | "desktop";
  step: 1 | 2 | 3 | 4;           // 4 = final restaurant page
  confirmed: { legal: boolean; banking: boolean; menu: boolean };
  published: boolean;            // set by POST /publish; gates the read-only page's "copy link"
  feedback_submitted: boolean;   // true once feedback was given (so the form is not reshown on resume)
  csat: number | null;           // 1..5 if feedback was given
  legal: LegalBlock;
  banking: BankingBlock;
  menu: MenuBlock;
}
```

## Endpoints

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/onboarding` | `{ locale?, device? }` | `{ id }` |
| GET | `/api/onboarding/{id}` | — | `Onboarding` |
| POST | `/api/onboarding/{id}/legal/parse` | multipart: `files[]`, `note?` | `LegalBlock` |
| PUT | `/api/onboarding/{id}/legal` | `LegalBlock` (edited fields) | `LegalBlock` |
| POST | `/api/onboarding/{id}/banking/parse` | multipart: `files[]`, `note?` | `BankingBlock` |
| PUT | `/api/onboarding/{id}/banking` | `BankingBlock` | `BankingBlock` |
| POST | `/api/onboarding/{id}/menu/parse` | multipart: `files[]`, `note?` | `MenuBlock` (merged) |
| PUT | `/api/onboarding/{id}/menu` | `MenuBlock` | `MenuBlock` |
| POST | `/api/onboarding/{id}/confirm` | `{ step }` | `Onboarding` (advanced) |
| POST | `/api/onboarding/{id}/publish` | — | `Onboarding` (`published: true`) |
| POST | `/api/onboarding/{id}/feedback` | `{ csat: 1..5, answers: {...} }` | `{ ok: true }` |
| GET | `/api/onboarding/{id}/restaurant` | — | `Onboarding` (read-only view; same shape) |
| POST | `/api/events` | `{ events: AnalyticsEvent[] }` | `{ ok: true }` |
| GET | `/api/admin/onboardings` | — | `AdminOnboardingRow[]` |
| GET | `/api/admin/metrics` | — | `AdminMetrics` |

### Parse semantics
- **Parse runs in a detached background task.** A parse first sets the block to `status: "parsing"`
  in the DB, then runs the AI work in a background task with its OWN db session, so it finishes even if
  the page is reloaded mid-parse. The parse POST still awaits that task and returns the final block to
  the active request (`ready`/`couldnt_parse`; menu also returns `skipped_duplicates`). On (re)load, if
  `GET /onboarding/{id}` shows any block with `status: "parsing"`, the client **polls** `GET` until it
  resolves — this is what keeps the loading state visible after a refresh. In-process for now; a durable
  worker queue (Redis) is the production upgrade.
- **Re-parse merge:** re-calling `parse` on a step never overwrites fields whose `provenance` is
  `user_edited`/`user_added`/`user_confirmed`. New menu items arrive flagged; conflicts are surfaced,
  not auto-applied. (Conflict UI is polish; "fill empties only" is the minimum.)
- **Registry is non-blocking:** `legal/parse` returns `Ready` even if the registry call fails;
  `registry` is populated when it succeeds.

### Crash-safety
Any model failure (refusal / malformed JSON / timeout / 429) yields a block with
`status: "couldnt_parse"` and whatever `partial` fields were recovered, never a 5xx that blanks the UI.

## Analytics events

`POST /api/events` accepts a batch. Every event carries the global props; the server also emits
server-side events (parse, registry, validation, cost). The frontend emits UI events.

```ts
interface AnalyticsEvent {
  name: string;                  // see taxonomy below
  onboarding_id: string;
  // global props (attach to every event):
  session_id: string;
  device: "mobile" | "desktop";
  locale: "fr" | "en";
  schema_version: number;
  ts: string;                    // ISO 8601
  props?: Record<string, unknown>;
}
```

Taxonomy (names + the key props that make metrics computable):
- `onboarding_started`
- `step_viewed` `{ step }`
- `file_uploaded` `{ step, file_type, bytes, upload_index }`
- `parse_completed` `{ step, doc_type, model, tokens_in, tokens_out, latency_ms, cost_eur, over_cost_cap }` — emitted **server-side**, once per model usage; `cost_eur` powers the admin AI economics, `over_cost_cap` flags a usage above `COST_CAP_EUR`.
- `field_resolved` `{ step, doc_type: "legal"|"banking"|"menu", field_name, parsed_value_present, confidence, resolution: "accepted_as_is"|"edited"|"cleared"|"added_manually"|"left_empty" }` — emitted **per parsed field when its step is confirmed** (not only on edit). `parsed_value_present` = whether the parser originally returned a value. The admin `auto_fill_acceptance` is computed from this; it buckets by `doc_type`.
- `menu_group_resolved` `{ group_name, items_parsed, items_final, items_added_manually, items_edited, items_removed, low_confidence_items }`
- `menu_usable_reached` `{ items_count }`
- `registry_verification_result` `{ identifier_type, lookup_status, name_match, latency_ms, cached }`
- `validation_result` `{ validator, passed, field_name }`
- `error_shown` `{ step, error_type }`
- `step_confirmed` `{ step, duration_ms }`
- `reparse_requested` `{ step }`
- `abandonment` `{ last_step, last_action, max_step_reached, elapsed_ms }` — reserved; not emitted yet. The admin funnel drop-off is derived server-side from `step_viewed`/`step_confirmed` timestamps, so this event is not required for current metrics.
- `onboarding_completed` `{ duration_ms }`
- `feedback_submitted` `{ csat }`

## Admin shapes

```ts
interface AdminOnboardingRow {
  id: string; status: string; device: "mobile"|"desktop";
  step: number; created_at: string; ttv_ms: number | null;
  ai_cost_eur: number; registry_status: string | null; csat: number | null;
}

interface AdminMetrics {
  funnel: { step: string; mobile: number; desktop: number }[];   // stages: started, legal_done, banking_done, menu_done, publishable
  ai_cost: { per_publishable_eur: number; by_model: Record<string, number>; by_step: Record<string, number> }; // by_step keys: legal, banking, menu
  quality: { auto_fill_acceptance: Record<"legal"|"banking"|"menu", number>;
             menu_hand_added_share: number; registry_success_rate: number; low_confidence_rate: number };
  friction: { step: string; drop_off: number /* ratio 0..1 */; top_reason: string | null; median_ms: number | null }[];
}
```

A "publishable" onboarding = completed AND legal+banking valid AND menu has ≥1 confirmed group with
≥1 item. This is the North Star unit.
