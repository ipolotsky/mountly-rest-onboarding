# Conventions

Keep the codebase transparent and readable. Optimize for the next developer.

## General
- No comments that explain *what* the code does; the code should read clearly on its own. Comments
  only for genuinely non-obvious *why*.
- Strict typing everywhere (Python type hints + mypy-clean intent; TypeScript strict).
- Full words in names, no abbreviations (`organization`, not `org`; `repository`, not `repo`).
  Exceptions: single-letter lambda args; `compare(a, b)` where the entity does not matter.
- In lambdas/inline functions: one arg → `x`; two args where one is an index → `x` and `i`.
- Always brace conditional/loop bodies, even single statements.
- No trace of AI authorship anywhere (code, text, comments, commits).

## Backend (Python / FastAPI)
- Layering: **HTTP handler → `OnboardingService` → graph/parsers/validators**. Handlers contain no
  AI/document logic, so chat can be added later without touching the core (see ARCHITECTURE.md).
- The only module that calls Claude is `llm.py`. Model per task comes from config — never hardcode a
  model id elsewhere.
- Every external call (Claude, registry) is wrapped so failure degrades to a typed result, never a 5xx.
- Pydantic models mirror [docs/API_CONTRACT.md](API_CONTRACT.md) exactly.
- Members ordered: constants, properties, fields, constructor, methods; public before private;
  caller above callee.

## Frontend (TypeScript / Vue 3)
- Named exports only (except where a framework requires default).
- `interface` over `type`; object type members separated by `;` including the last.
- No destructuring except rest/spread to drop fields.
- Use `?.` for nullable calls; `==`/`!=` only against `null`; `===`/`!==` otherwise; `!!` to coerce.
- Components: `export const XxxZzz: React.FC` — N/A here; Vue 3 `<script setup lang="ts">` SFCs, one
  component per file, filename = component name. Props typed via `defineProps<XxxZzzProps>()`.
- If a component has `value` + `onChange`-style props, they come first.
- File order: constants, types, props, component, helpers.
- TS types for API objects come from the shared contract; do not redefine ad-hoc shapes.

## Testing
- Backend: `pytest`. Validators and price parsing are pure unit tests on the **real sample
  identifiers**. Pipeline e2e mocks `llm.py` + `registry.py` with **recorded golden fixtures**
  (deterministic, no API key in CI). A `test_crash_from_empty` proves the assembler/UI render from an
  all-null state. `make test-live` runs the real Claude API against all 6 menu samples (run before
  submitting; capture screenshots in the README).
- Golden fixtures are **regenerated from real API calls** by `backend/tests/scripts/regen_fixtures.py`
  and schema-validated, so they cannot silently drift from the Pydantic schema.
- Frontend: component tests for the menu builder interactions (add/remove group+item, price-less,
  variants, re-parse merge).

## Adding a feature
1. Update [docs/API_CONTRACT.md](API_CONTRACT.md) if the wire shape changes.
2. Backend: extend the service/graph (not the handlers); add validators/tests.
3. Frontend: extend the relevant view/components against the contract types.
4. Update [CONTEXT.md](../CONTEXT.md) "Current status" + "Next".
