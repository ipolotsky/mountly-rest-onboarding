# Context & handoff

**Read this first.** It is the living status of the project: what exists, what is next, and where to
continue. Keep it up to date as you ship.

## What this is

A take-home for Mountly (AI Product Engineer). A document-driven restaurant onboarding flow. See
[README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md). The full product/UX/metrics plan lives
in the planning notes; the durable decisions are distilled into [docs/DECISIONS.md](docs/DECISIONS.md).

## Build order (de-risk the graded axes first)

1. **AI core + ingest, run the 6 real menu samples and eyeball the output** — the biggest unknown.
2. Wizard + start screen + the per-field status state machine + crash-safe rendering from empty.
3. Editable **menu builder** (highest-graded UI) + the read-only restaurant page.
4. Admin metrics dashboard + CI + deploy (docker, like Aivus) + the planning email + a README results
   section with screenshots from the real samples.

## Current status

- [x] Repo foundation: root docs, API contract, conventions, decision log, docker scaffolding (Aivus
      pattern), Makefile, env templates.
- [x] Frontend (`frontend/`): Vue 3 + Vite + TS (strict) + Tailwind/Flowbite. 6 views (Start consent,
      WizardLegal, WizardBanking, WizardMenu builder, RestaurantPage, Admin) + 28 components. Pinia
      store, `useOnboarding`/`useAnalytics`, FR/EN i18n, contract-typed API client. Builds clean
      (`vue-tsc` strict), lints clean, 112 Vitest tests pass. State rehydrates from the server by
      `onboarding_id` in localStorage; renders crash-safe from an all-missing state.
- [x] Backend core (`backend/`): FastAPI + LangGraph + parsers/validators/registry/merge/analytics +
      `OnboardingService` + file storage + admin metrics. `converse` node stubbed for chat. **78 tests
      pass, 3 live skipped, ruff clean, routes match the contract** (no contract deviations).
- [x] Integration (build level): backend tests green, frontend `vite build` green, both compose files
      validate, CI wired (`.github/workflows/ci.yml`) + deploy (`deploy.yml`, SSH + docker like Aivus).
- [x] Independent QA + two fix rounds, re-verified green. Core flow WORKS: multi-onboarding e2e (3
      distinct restaurants), live uvicorn server degrades to `couldnt_parse` with no API key (no 500s),
      validators correct on the real identifiers, crash-safe from empty (including from an all-NULL DB
      row). Fixed along the way: the admin-metrics layer (auto-fill acceptance was always 0; friction
      drop-off rendered as a raw count; client/server analytics double-emit; PUT legal/banking didn't
      re-validate server-side); the 15-item UX polish round; AI calls made fully async so the app never
      blocks during a parse; parse made to survive a page refresh (the block persists `parsing`, the work
      runs in a detached task with its own session, the client polls until it resolves); a detached parse
      that errors now reconciles to `couldnt_parse` instead of sticking in `parsing`; resumed sessions
      rehydrate the parsed snapshot so auto-fill acceptance is not under-counted. **Final: backend 72
      passed / 3 live skipped, frontend 78 passed, both lint clean, both `pytest`/`build` green, both
      Docker images build. Now backend 78 passed / 3 live skipped, frontend 112 passed.**
- [x] Live end-to-end VERIFIED on the real documents via `pytest -m live` (legal + banking + menu, all
      pass). Legal/banking pull correct values (SIREN 913472056, SAS, Morzine, MORAND Céline; IBAN
      FR76…0174, BIC AGRIFRPP878). All 7 real menu images (`menu_1..7`) parse to `ready` with correct
      sections, items and original-string prices — including the hard ones (handwritten chalkboard, glare
      wine list, dark phone screenshots); ~€0.33 total on Opus 4.8 (~€0.047/menu). Two fixes landed from
      the first live run (strict-grammar timeout → JSON-prompt extraction; IBAN/BIC/SIREN normalization) —
      see DECISIONS.md. Remaining: `make up` to click through the full wizard UI; deploy; README screenshots.
- [x] Admin analytics reworked into an operator dashboard: outcome-based activation funnel with per-stage
      drop-off, AI economics (cost per publishable, by model/step), friction per step (drop-off, badge
      reasons, real median dwell time from step_viewed→step_confirmed), time-to-value distribution
      histogram, status badges, clickable onboarding rows, and a customer-feedback (CSAT) panel. Added a
      demo seeder (`make seed`, 40 onboardings + full event taxonomy). CI green; Deploy workflow green on
      push to `main` (traefik v3.6). README expanded and a proprietary LICENSE added.

> Update the checkboxes and the "Next" list below as you go.

## Conventions you must follow

- The API contract in [docs/API_CONTRACT.md](docs/API_CONTRACT.md) is the source of truth shared by
  backend and frontend. Change it there first, then both sides.
- All AI/document logic lives in the service + graph layer, **never** in HTTP handlers, so chat can be
  added later without touching the core (see ARCHITECTURE.md).
- Code style: [docs/CONVENTIONS.md](docs/CONVENTIONS.md).

## How to add the next feature (e.g. chat onboarding)

1. Add the `converse` graph node (the stub is already there) — it routes to the existing parse/
   validate nodes; it does not reimplement them.
2. Add one endpoint `POST /api/onboarding/{id}/chat`.
3. Add a chat view on the frontend that reuses the existing field/menu components.
   Nothing in the core changes.

## Next

1. **Run it live.** Put `ANTHROPIC_API_KEY` in `.env`, `make up`, open http://localhost:5173, and walk
   the wizard end-to-end against the real documents. (App + routes are already exercised by the backend
   TestClient suite; this confirms live Claude parsing + the docker runtime.)
2. **Drop the real sample files** into `backend/tests/fixtures/samples/` (`mock_kbis.pdf`,
   `mock_rib.pdf`, and the menu images). The deterministic suite passes without them (hand-authored
   golden fixtures); `make test-live` and `regen_fixtures.py` need them. Not in the repo because they
   were provided out-of-band (GDrive / attachments).
3. **Deploy — configured and green.** The Deploy workflow runs on push to `main` (SSH + production
   compose, traefik v3.6) and is passing. Remaining: put the public URL into the README "Live demo" line.
4. Run `make test-live` on all 6 menu samples; add a "Results" section to the README with screenshots
   (evidence of graceful degradation on the chalkboard / dark screenshot).
5. Send the short planning email (draft/outline lives in the planning notes).
