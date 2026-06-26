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
      (`vue-tsc` strict), lints clean, 26 Vitest tests pass. State rehydrates from the server by
      `onboarding_id` in localStorage; renders crash-safe from an all-missing state.
- [x] Backend core (`backend/`): FastAPI + LangGraph + parsers/validators/registry/merge/analytics +
      `OnboardingService` + file storage + admin metrics. `converse` node stubbed for chat. **43 tests
      pass, 3 live skipped, ruff clean, routes match the contract** (verified by the tech-lead, no
      contract deviations).
- [x] Integration (build level): backend tests green, frontend `vite build` green, both compose files
      validate, CI wired (`.github/workflows/ci.yml`) + deploy (`deploy.yml`, SSH + docker like Aivus).
- [x] Independent QA audit (3 fresh agents) + fix round, re-verified by the tech-lead. Core flow WORKS:
      multi-onboarding e2e (3 distinct restaurants), live uvicorn server degrades to `couldnt_parse`
      with no API key (no 500s), validators correct on the real identifiers, crash-safe from empty. The
      bugs the audit found — all in the admin-metrics layer (auto-fill acceptance was always 0; friction
      drop-off rendered as a raw count; client/server analytics double-emit; PUT legal/banking didn't
      re-validate server-side) — are fixed and tested. **Final: backend 54 passed / 3 live skipped,
      frontend 39 passed, both lint clean, both `pytest`/`build` green, both Docker images build.**
- [x] Live end-to-end VERIFIED on the real documents via `pytest -m live` (legal + banking + menu, all
      pass). Legal/banking pull correct values (SIREN 913472056, SAS, Morzine, MORAND Céline; IBAN
      FR76…0174, BIC AGRIFRPP878). All 7 real menu images (`menu_1..7`) parse to `ready` with correct
      sections, items and original-string prices — including the hard ones (handwritten chalkboard, glare
      wine list, dark phone screenshots); ~€0.33 total on Opus 4.8 (~€0.047/menu). Two fixes landed from
      the first live run (strict-grammar timeout → JSON-prompt extraction; IBAN/BIC/SIREN normalization) —
      see DECISIONS.md. Remaining: `make up` to click through the full wizard UI; deploy; README screenshots.

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
3. **Deploy.** On the server: clone the repo, create `.env` (DOMAIN, ACME_EMAIL) and
   `.envs/.production/{.app,.postgres}` from the templates, then `make deploy`. In GitHub, set the
   `SSH_HOST/SSH_USER/SSH_KEY/DEPLOY_PATH` secrets so the Deploy workflow runs on push to `main`.
4. Run `make test-live` on all 6 menu samples; add a "Results" section to the README with screenshots
   (evidence of graceful degradation on the chalkboard / dark screenshot).
5. Send the short planning email (draft/outline lives in the planning notes).
