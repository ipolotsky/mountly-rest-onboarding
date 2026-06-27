# Restaurant Onboarding

Document-driven onboarding for French restaurants: upload your existing paperwork, review a pre-filled listing instead of typing it from scratch.

[![CI](https://img.shields.io/github/actions/workflow/status/ipolotsky/mountly-rest-onboarding/ci.yml?label=CI)](https://github.com/ipolotsky/mountly-rest-onboarding/actions)
![Vue 3](https://img.shields.io/badge/Vue-3-42b883)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178c6)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab)
![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-1c3c3c)
![Claude](https://img.shields.io/badge/Claude-Opus%204.8%20%2F%20Sonnet%204.6-d97757)
![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red)

## What it does

A restaurant owner opens the app and walks through four screens, each connected by a single "Looks good" button. There is no back-and-forth form filling: at every step the owner uploads a document, the app reads it with Claude, and the extracted fields appear pre-filled for review.

1. **Legal.** Upload a Kbis or SIRENE extract. The app pulls out the legal name, SIREN, SIRET, legal form, registered address, and legal representative, validates the identifiers, and cross-checks the SIREN against the French business registry.
2. **Banking.** Upload a RIB. The app pulls out the account holder, bank name, IBAN, and BIC, validates the IBAN and BIC, and warns if the account holder does not match the legal name.
3. **Menu.** Upload one or more menu photos or PDFs. The app builds an editable menu of sections, dishes, descriptions, and prices, flags anything it read with low confidence, and lets the owner fix it in place.
4. **Restaurant page.** A read-only listing assembled from the reviewed data, with per-block status badges and a "Business verified" mark when the registry confirmed the company.

Everything autosaves. A session survives a refresh, a crash, or going offline, and resumes at the right step. The owner reviews; they do not type.

## The flow

The app has six routes: the four-screen wizard (`/`, `/onboarding/legal`, `/onboarding/banking`, `/onboarding/menu`), the final `/restaurant` page, an `/admin` dashboard, and a catch-all that redirects to the start. Each wizard step's "Looks good" button routes to the next one.

### 1. Legal

Six fields in fixed order: `legal_name`, `siren`, `siret`, `legal_form`, `registered_address`, `legal_representative`.

SIREN and SIRET are validated client-side; the Continue button stays disabled until they pass, and invalid fields show an inline error. Empty values are allowed and do not block. If the document could not be parsed, "Enter manually" reveals the editable fields. When the registry confirms the SIREN, it shows a "Verified with the business registry" note.

### 2. Banking

Four fields in fixed order: `account_holder`, `bank_name`, `iban`, `bic`.

IBAN and BIC are validated client-side and gate the Continue button the same way. If the parsed account holder differs from the legal name captured on the previous step, an amber "Holder differs from the legal name - please check" warning appears above the fields.

### 3. Menu

The menu upload accepts multiple files at once (legal and banking accept one). Each item carries a name, a description, and prices, where a price is a list of label-plus-amount variants. Items live inside named sections.

The menu builder is fully editable:

- add and remove sections, add and remove dishes, edit name, description, and price per dish;
- pressing Enter on a new dish keeps focus so several can be added quickly;
- removing a section is non-destructive: its dishes move to a "Sans catégorie" (Uncategorized) catch-all and an Undo toast appears for seven seconds;
- section and dish deletions ask for confirmation first;
- a review banner counts items flagged low-confidence and opens a modal that steps through them with Keep / Fix / Remove;
- re-parsing additional files diffs the menu and highlights brand-new items in green and content-changed items in blue (the highlight fades after five seconds);
- duplicate files are detected by the backend and surfaced as a dismissable "Already added, file skipped." toast.

Inline text edits are buffered locally and committed on blur or Enter, so typing never triggers a per-keystroke save that would drop characters or jump the cursor. Prices accept either a single amount or an expandable size/variant table; an empty price renders as an "On site" chip and "Price on site" on the final page. Amounts are normalized to European format: comma decimal, at most two decimals, € on display.

Continue requires at least one item across all sections and that no document is still parsing.

### 4. Restaurant page

A read-only listing with three blocks (Business, Banking, Menu) rendered from the same field order as the wizard. Missing values render as an italic grey placeholder ("— non renseigné —" / "— not provided —"). There is no inline editing here.

Each block carries a status pill with three variants: "Ready", "Couldn't parse" (also used for an empty block), and "Business verified" — the last shown only when the legal block's registry status is `match`.

For the owner, the page also exposes Edit listing, Publish (which gates the Copy-link action), and a CSAT feedback form. A shared deep-link `/restaurant?id=…` loads any onboarding read-only without touching the visitor's own session or analytics.

The whole UI is bilingual (FR/EN, French default and fallback). The initial locale comes from `localStorage`, then the browser language; a FR/EN toggle in the header switches and persists it.

## How documents are verified

This is the core of the product. A document is never trusted blindly; it goes through extraction, checksum validation, cross-document consistency, and registry enrichment, and degrades gracefully at every stage.

**LLM extraction.** Claude reads each document. Models are configured per task: `claude-sonnet-4-6` for legal and banking, `claude-opus-4-8` for menus. PDFs are sent as document blocks and images (JPEG/PNG/WebP/GIF) as image blocks; uploads are capped at 20 MB. Rather than relying on a strict structured-output grammar (which can return a 400 "Grammar compilation timed out" on richer schemas), the pipeline prompts for a single JSON object, parses it leniently, and validates it with Pydantic.

**Checksum validation.** Extracted identifiers are checked, not assumed:

- SIREN: exactly nine digits, not all zeros, passing the Luhn checksum;
- SIRET: exactly fourteen digits, not all zeros, passing the Luhn checksum;
- IBAN: ISO 7064 mod-97, enforcing France's length of 27;
- BIC: format-validated by regex.

Before validation or storage, SIREN/SIRET/IBAN/BIC are stripped to `[A-Z0-9]` and uppercased to drop spaces, dots, dashes, and invisible characters such as zero-width spaces that would otherwise corrupt a checksum or a real bank transfer. The same canonicalization runs again on save.

**Cross-document consistency.** The banking account holder is compared against the legal name. Both names are normalized (whitespace collapsed, uppercased) before comparison; the result is stored on the banking block and surfaces as the "Holder differs" warning when they disagree.

**French business registry enrichment.** A valid SIREN is looked up against `recherche-entreprises.api.gouv.fr` with a 3-second timeout. The SIREN is Luhn-checked before any HTTP call; a missing or invalid SIREN yields registry status `skipped`. The client has a circuit breaker: three consecutive failures open it for thirty seconds, during which lookups return `unavailable` without making a request; results are cached per SIREN. If the registry is down — timeout, non-2xx, or open circuit — the legal block stays Ready; only the registry sub-status reflects the outage.

**Graceful degradation.** A refusal, a timeout, a 429, or any other error degrades the affected block to "Couldn't parse" rather than failing the request. A legal block reaches Ready only with both a legal name and a SIREN; banking needs both an account holder and an IBAN; a menu needs at least one item.

**Confidence-driven review.** Each field carries a confidence; below 0.6 it is marked `low_confidence` instead of `present`. The menu review queue collects these so the owner confirms or fixes them before publishing.

## Architecture in one line

One reusable AI core — a LangGraph `StateGraph` over Claude (ingest → parse → validate → enrich → merge → assemble) — driven by the wizard today, with a deliberately orphaned `converse` node reserved for a chat front-door tomorrow. The pipeline is transport-agnostic; the same parse/validate/merge nodes would back a chat endpoint without change. See [ARCHITECTURE.md](ARCHITECTURE.md).

Parsing runs in a detached asyncio task with its own database session, so a client disconnect or page refresh cancels only the awaiting request, not the work: the task runs to completion, writes its result, and a reloaded page polls the row to observe `parsing → ready` / `couldnt_parse`. The frontend polls every 1.5 seconds up to a 120-second cap; on timeout any block still parsing is marked `couldnt_parse`.

## Admin analytics

`/admin` is an operator dashboard built from a first-party analytics event stream. It surfaces:

- **Activation funnel** — five stages (started, legal done, banking done, menu done, publishable), split mobile vs desktop, with per-stage conversion and drop-off between stages.
- **AI economics** — cost per publishable onboarding, plus cost broken down by model and by step. Cost is tracked per parse: tokens × per-model pricing, converted USD→EUR, with an over-cap flag.
- **Friction per step** — drop-off, the most frequent error reason (shown as a badge), and median dwell time (measured from step-viewed to step-confirmed).
- **Time-to-value distribution** — a four-bucket histogram of completion time with median and p90 overlays.
- **Onboardings table** — id, status, device, time-to-value, AI cost, registry status, and CSAT, each row linking to the restaurant result.
- **Customer feedback** — CSAT scores with the free-text "what helped" / "what to improve" answers, each entry linking to its restaurant result.

Activation is the customer clicking "Looks good" on the menu review (step 4); publishing is a decoupled convenience and never drives the funnel.

A demo seeder fills a local database with 40 representative onboardings and the full event taxonomy (started, step viewed, step confirmed, parse completed, registry verification, errors, completed) using a fixed random seed for reproducibility. Run it with `make seed`.

## Tech stack

**Frontend.** Vue 3.5, vue-router 4.4, Pinia 2.2, vue-i18n 10, axios 1.7, Flowbite 2.5. Tooling: Vite 5.4, TypeScript 5.6, vue-tsc 2.1, Tailwind CSS 3.4 + PostCSS + autoprefixer, Vitest 2.1 with `@vue/test-utils` and jsdom, ESLint 8.57. 112 tests across 21 files.

**Backend.** Python 3.11+, FastAPI 0.115+, uvicorn, gunicorn, Pydantic 2.9+ with pydantic-settings, SQLAlchemy 2.0, psycopg 3, anthropic 0.40+, langgraph 0.2+, httpx, python-multipart. Lint with ruff, test with pytest + pytest-asyncio. 78 tests pass, 3 skipped (the live tests that hit the real Claude API and need `ANTHROPIC_API_KEY`).

## Quickstart

```sh
make up
```

This builds the full local stack: PostgreSQL, the FastAPI app on `:8000`, and the Vite dev server on `:5173`. Open `http://localhost:5173`.

Live document parsing needs a Claude API key:

```sh
export ANTHROPIC_API_KEY=sk-ant-...
```

Fill the local database with demo onboardings and analytics events:

```sh
make seed
```

Run the test suites (no API key required):

```sh
make test
```

`make test-live` runs the suite against the real Claude API on the sample menus; it requires `ANTHROPIC_API_KEY`. Other useful targets: `make dev-backend` (Postgres + app only), `make logs`, `make sh-app`, `make fmt`, `make down`.

## Deployment

The production stack runs under Docker Compose: Traefik v3.6 terminates TLS via Let's Encrypt (HTTP-01 challenge, HTTP→HTTPS redirect) and routes `Host(DOMAIN) && PathPrefix(/api)` to the FastAPI app and `Host(DOMAIN)` to the static SPA. The frontend is a multi-stage build — Node 20 build, served by nginx 1.27 with SPA fallback, long-lived asset caching, and gzip. PostgreSQL 16 holds data and backups. Secrets come from `./.envs/.production/`.

CI runs on every push and pull request: a backend job (ruff + pytest) and a frontend job (ESLint, strict `vue-tsc` type-check, Vite build, Vitest). Deployment triggers on push to `main` and on manual dispatch: it SSHes to the server, fast-forwards `main`, and runs `docker compose -f docker-compose.production.yml up -d --build`. Docker images pin Python 3.12.

**Live demo:** _add the deployed URL here_

## Project layout

```
.
├── backend/
│   ├── app/
│   │   ├── graph.py        # LangGraph pipeline (ingest → … → assemble, converse)
│   │   ├── llm.py          # Claude client; the only LLM touchpoint
│   │   ├── parsers.py      # per-document extraction
│   │   ├── validators.py   # Luhn, IBAN mod-97, BIC, name normalization
│   │   ├── registry.py     # French registry client + circuit breaker
│   │   ├── ingest.py       # file classification and limits
│   │   ├── merge.py        # menu merge that preserves user edits
│   │   ├── service.py      # detached parsing, persistence, analytics events
│   │   ├── analytics.py    # admin metrics
│   │   └── config.py       # per-task models, pricing, thresholds
│   ├── scripts/seed_demo.py
│   └── tests/
├── frontend/
│   └── src/
│       ├── router/
│       ├── stores/onboarding.ts
│       ├── views/          # wizard steps, RestaurantPage, Admin
│       ├── components/     # MenuBuilder, ParseStatus, charts, …
│       ├── domain/         # upload limits, price formatting, menu diff
│       └── i18n/
├── docker-compose.local.yml
├── docker-compose.production.yml
├── Makefile
└── ARCHITECTURE.md
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — how the system fits together and how chat plugs into the same core.
- [docs/API_CONTRACT.md](docs/API_CONTRACT.md) — the REST contract and shared data shapes (source of truth for backend and frontend).
- [docs/DECISIONS.md](docs/DECISIONS.md) — decision log: why things are the way they are.
- [docs/CONVENTIONS.md](docs/CONVENTIONS.md) — code conventions and how to add a feature.
- [CONTEXT.md](CONTEXT.md) — current status and handoff notes.

## Roadmap

- [ ] **SIRET↔SIREN cross-validation** — confirm the SIRET's nine-digit prefix matches the SIREN within a document, not just each checksum in isolation.
- [ ] **Chat onboarding on the same AI core** — a conversational front-door reusing the existing parse/validate/merge nodes, A/B tested against the wizard.
- [ ] **Authoritative registries** — move from `recherche-entreprises` to INSEE / INPI sources and extend coverage beyond France.
- [ ] **Full encryption at rest** — encrypt stored documents and extracted financial identifiers.
- [ ] **Formal GDPR compliance** — data retention, export, and deletion workflows for personal and business data.

## License

Proprietary. This software and its contents are the property of Mountly. All rights reserved. No use, copying, modification, or distribution without prior written permission from Mountly. See [LICENSE](LICENSE).
