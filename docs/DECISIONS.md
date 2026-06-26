# Decision log

Short, dated rationale for the choices that aren't obvious from the code. Append, don't rewrite.

## Stack: FastAPI + Vue 3 + LangGraph + Claude
Close to Mountly's stack (Python + Vue), and LangGraph lives in Python. FastAPI is async-native for
AI work. We deliberately did **not** use Frappe for the take-home: heavy to stand up and deploy, it
would burn time on infra instead of the graded menu UX. In production this onboarding is best kept as
a standalone AI microservice the Frappe monolith calls over HTTP, so a port is cheap or unnecessary.

## One AI core, chat-ready
A single LangGraph graph + `OnboardingService` drive the wizard now and a chat later. All AI/document
logic stays in the service/graph layer; HTTP handlers are thin. Adding chat = one endpoint + the
already-stubbed `converse` node, with no change to the core. (See ARCHITECTURE.md.)

## Models swappable in one line
Per-task model from config (`MODEL_LEGAL`, `MODEL_BANKING`, `MODEL_MENU`), used only via `llm.py`.
Defaults: Sonnet 4.6 for the clean Kbis/RIB PDFs, Opus 4.8 for the hard menu vision. Swapping a model
or provider is one env line.

## Ingest branches by file type
Claude `document` blocks are PDF/text only. Most menu uploads are photos/screenshots, so `ingest`
sends **PDF → document block, image → image block**. Getting this wrong silently breaks 5 of the 6
menu samples.

## Prices are strings, never floats
European decimals (`12,50`), multiple prices per item (glass/bottle, 25cl/50cl), and price-less items
are all valid. `PriceVariant.amount` keeps the original string; `null` means no price. A naive
`float()` would crash or corrupt data.

## Status model
Per-field `present | low_confidence | missing`; per-block `ready | couldnt_parse`. Low-confidence is
"ready with an amber flag", not "couldn't parse". Missing renders a placeholder. The final page must
render from a fully-empty state — there is a test for it. This is the second-most-graded behavior, so
it is specified, not improvised.

## French registry is non-blocking enrichment
`recherche-entreprises.api.gouv.fr` is free and needs no auth. We verify the SIREN and enrich legal
fields, but with a short timeout + circuit breaker: a block is **Ready** even if the registry is down,
so the demo never depends on a live external API. Authoritative registries (INSEE/INPI) and non-FR
countries are roadmap (add only free ones first).

## Analytics: one abstraction, two sinks; Amplitude is a stub
`track(event)` always writes the `event` table (which powers the admin dashboard) and forwards to
Amplitude only if a key is set. We scaffold the Amplitude path but do not provision a live account —
the abstraction is the point, not the integration.

## Deployment: docker like Aivus, secrets on the server
Not Cloud Run. `docker-compose.production.yml` with `traefik` (TLS via Let's Encrypt), `web` (nginx
SPA), `app` (FastAPI), `postgres`. Real secrets are env files on the server under `.envs/.production/`;
the repo holds only templates in `.envs.production.example/` and compose-level vars in `.env.example`.
This mirrors the Aivus project's containerization pattern. SQLite is used for local/test speed;
SQLAlchemy keeps the swap trivial.

## Live-test findings: JSON-prompt extraction + identifier normalization (2026-06-26)
The first live run against the real Kbis/RIB surfaced two issues, both fixed:
- **Legal parse failed with `400 Grammar compilation timed out`.** That is the strict structured-output
  path (`messages.parse` / `output_config.format` json_schema): on the richer 12-field legal schema the
  API's grammar compiler timed out (the 8-field banking schema compiled fine). We dropped strict grammar
  entirely — `llm.extract` now prompts for a JSON object matching the schema and validates it with
  Pydantic. One call, no grammar compilation, and it still degrades to `couldnt_parse` on any failure.
  Lesson: **don't rely on strict structured-output grammar for non-trivial extraction schemas.**
- **The IBAN came back with a stray internal space** (`FR76…301 74`), which would break both display and
  the mod-97 check. The parser now normalizes IBAN/BIC/SIREN/SIRET (strip whitespace, uppercase) so the
  stored value is canonical regardless of how the model spaced it.
Verified live afterwards: legal + banking parse to the correct values (SAVEURS DU SOLEIL LEVANT, SIREN
913472056, SAS, Morzine, MORAND Céline; IBAN FR7618306000457021845630174, BIC AGRIFRPP878), ~€0.015 +
~€0.010 per parse on Sonnet 4.6.

## Independent QA audit & metrics-layer fixes (2026-06-26)
After the first build, three independent agents (backend QA, frontend QA, integration reviewer) audited
the whole thing by actually running it — multi-onboarding end-to-end, a live uvicorn server, build/lint/
tests on both sides. The core flow was sound, but the audit found a cluster of real bugs in the admin
**metrics** layer (the product's top-priority feature): `auto_fill_acceptance` was always 0 (the
`field_resolved` event lacked `doc_type` and hardcoded `resolution: "edited"`, and only fired on edit);
friction `drop_off` was a raw count rendered as a percent ("300 %"); client and server double-emitted
lifecycle events and the client's `parse_completed` polluted `ai_cost.by_step`; and `PUT /legal`/`/banking`
trusted client-supplied `valid` flags. All fixed: `field_resolved` is now emitted per parsed field at
confirm with `doc_type` + a real `resolution` + parser-origin `parsed_value_present`; `drop_off` is a 0..1
ratio; lifecycle events are client-owned, cost is server-owned; the server re-validates on save. Funnel
stages renamed to outcome-based labels. The take-away encoded here: **the admin dashboard is a thin read
over the `event` taxonomy — keep the emitted events and the metric computations in lockstep, or panels
silently read zero.**

## Deliberate over-delivery (and what we cut)
Admin metrics + an Amplitude scaffold, i18n FR/EN, GDPR consent, and the chat-ready core are beyond
the literal brief; they are kept to demonstrate product range for a 50%-product role, but scoped:
Amplitude stubbed, i18n FR-primary, GDPR = consent + copy (real encryption-at-rest is roadmap), chat
not built. If time slips: drop the re-parse conflict UI (keep "fill empties"), drag reorder, EN
parity, and SSE (keep polling) — never the menu builder or the placeholder/status behavior.
