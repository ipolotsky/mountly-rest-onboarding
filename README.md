# Restaurant Onboarding

Onboarding flow that lets a French restaurant join a food-delivery marketplace by **uploading its
existing documents** (business registration, bank details, menu) and having the listing
**pre-filled automatically**, so the owner *reviews and confirms* instead of *typing*.

Three steps, then an assembled restaurant page:

1. **Legal entity** — upload a Kbis / SIRENE PDF → parsed legal name, SIREN/SIRET, legal form,
   registered address, legal representative (validated by checksum + the free French business
   registry).
2. **Banking** — upload a RIB PDF → account holder, bank name, IBAN, BIC (validated).
3. **Menu** — upload one or more photos / PDFs / screenshots → items grouped into sections, in an
   **editable menu builder** (add/remove group, add/remove item, fix prices, add missing dishes).
4. **Restaurant page** — read-only summary; each block shows **Ready** or **Couldn't parse**, with
   clean placeholders for anything missing.

The hard work is a single AI core (LangGraph over Claude) shared by the wizard today and a chat
onboarding tomorrow — see [ARCHITECTURE.md](ARCHITECTURE.md).

## Start here (for the next developer)

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — how the system fits together and why; how to add chat
  without churning the core.
- **[CONTEXT.md](CONTEXT.md)** — current status, what's done, what's next. **Read this first.**
- **[docs/API_CONTRACT.md](docs/API_CONTRACT.md)** — the REST contract + shared data shapes (the
  source of truth shared by backend and frontend).
- **[docs/CONVENTIONS.md](docs/CONVENTIONS.md)** — code conventions and how to add a feature.
- **[docs/DECISIONS.md](docs/DECISIONS.md)** — decision log (why things are the way they are).

## Layout

```
backend/     FastAPI + LangGraph AI core + parsers/validators/registry + tests   (owns /api)
frontend/    Vue 3 + Vite + Flowbite SPA (wizard, menu builder, admin)           (owns / )
docs/        API contract, conventions, decision log
.envs.production.example/   env templates; real secrets live on the server, never committed
docker-compose.local.yml    local dev (postgres + app hot-reload + vite)
docker-compose.production.yml  prod (traefik + web + app + postgres), mirrors the Aivus pattern
Makefile     common commands
```

## Quickstart (local)

```bash
cp .env.example .env                      # compose-level vars (local defaults are fine)
make up                                    # postgres + app (:8000) + web (:5173)
# open http://localhost:5173
```

You need an `ANTHROPIC_API_KEY` for live parsing. Without it, the deterministic test suite still
runs against recorded fixtures (see [docs/CONVENTIONS.md](docs/CONVENTIONS.md) → Testing).

## Deploy

Docker containerization mirroring the Aivus project: `docker-compose.production.yml` with `traefik`
(TLS via Let's Encrypt), `web`, `app`, `postgres`. Secrets are env files on the server under
`.envs/.production/` (templates in `.envs.production.example/`). See
[docs/DECISIONS.md](docs/DECISIONS.md) → Deployment.
