# Architecture

## One AI core, multiple front-doors

The valuable, reusable part is a single **AI core** that turns documents into structured, validated
onboarding data. It is transport-agnostic: it does not know whether it is driven by the step-by-step
wizard (built now) or by a chat assistant (planned). Both call the same service layer and the same
LangGraph graph.

```
Vue 3 SPA  ──REST (/api)──▶  FastAPI  ──▶  OnboardingService  ──▶  LangGraph core  ──▶  Claude
(wizard now; chat later)        │               │                       │                (vision/PDF +
                                │               │                       │                 structured output)
                                │               │                       ├─ ingest (PDF→document / image→image block)
                                │               │                       ├─ parse_legal / parse_banking / parse_menu
                                │               │                       ├─ validate (checksums + cross-doc)
                                │               │                       ├─ enrich_registry (non-blocking, FR)
                                │               │                       ├─ merge_menu
                                │               │                       └─ assemble
                                │               └─ analytics (event table + Amplitude sink stub)
                                └─ Postgres (onboarding state = source of truth)
```

## Why this shape (and how chat plugs in later)

The wizard endpoints (`/legal/parse`, `/banking/parse`, `/menu/parse`, `confirm`, …) are thin: they
call **`OnboardingService`** methods, which drive the **LangGraph graph**. Adding chat later is
purely additive:

- A new endpoint `POST /api/onboarding/{id}/chat` calls a new `converse` node already stubbed in the
  graph.
- The `converse` node reuses the exact same parse/validate/merge nodes and the same persisted
  `OnboardingState`. It only decides *which* node to run next and renders assistant turns + UI
  directives.
- **No change to the core, the schemas, the validators, the persistence, or the wizard.**

This is the rule for the backend: **keep all document/AI logic in the service + graph layer, never in
the HTTP handlers.** Handlers map HTTP ↔ service calls and nothing else.

## Components

- **`backend/app/llm.py`** — the only place that talks to Claude. Per-task model is chosen via
  config, so swapping a model (or provider) is one line. Wraps every call so a refusal / malformed
  JSON / timeout / 429 becomes a typed `ParseResult{status: "couldnt_parse", partial}` — the UI must
  always be able to render, never crash.
- **`backend/app/ingest.py`** — branches by file type: **PDF → `document` block; image → `image`
  block** (most menu uploads are photos/screenshots, not PDFs).
- **`backend/app/parsers.py`** — per-document Claude calls with JSON-Schema structured output.
- **`backend/app/validators.py`** — SIREN/SIRET Luhn, IBAN mod-97, BIC format, cross-doc holder vs
  legal name. Pure functions, fully unit-tested on the real sample identifiers.
- **`backend/app/registry.py`** — non-blocking enrichment via the free `recherche-entreprises.api.gouv.fr`
  (FR companies). Short timeout + circuit breaker; a block is still **Ready** if the registry is down.
- **`backend/app/graph.py`** — the LangGraph graph + `OnboardingState`.
- **`backend/app/service.py`** — `OnboardingService`: the transport-agnostic API the handlers use.
- **`backend/app/analytics.py`** — one `track(event)` abstraction → two sinks: the `event` table
  (powers the admin dashboard) and Amplitude (forwarded only if a key is set; otherwise a no-op stub).
- **`frontend/`** — Vue 3 SPA: the wizard, the editable menu builder, the read-only restaurant page,
  and the admin metrics dashboard.

## Status model (the second-most-graded behavior)

Per field: `present` | `low_confidence` | `missing`. Per block: `ready` if the minimum required
fields are present (low-confidence still counts as present, just flagged), `couldnt_parse` only if
parsing threw or returned nothing usable, `missing` data renders as a clean placeholder. The final
page renders correctly from a fully-empty state — there is a test for exactly that.

## Data model

One `onboarding` row (JSONB for `legal` / `banking` / `menu` + `step` + `locale` + `device`) and one
`event` row type (analytics / cost / feedback, by `kind`). SQLAlchemy; Postgres in prod, SQLite for
fast local/test runs. Shapes are defined once in [docs/API_CONTRACT.md](docs/API_CONTRACT.md) and
implemented as Pydantic models (backend) and TS types (frontend).

## Deployment

Mirrors the Aivus project: `docker-compose.production.yml` with `traefik` (TLS), `web` (nginx static
SPA), `app` (FastAPI), `postgres`. Secrets are env files on the server. See
[docs/DECISIONS.md](docs/DECISIONS.md).
