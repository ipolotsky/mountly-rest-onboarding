# App (FastAPI) production env. Copy to .envs/.production/.app on the server.
# Every value below except ANTHROPIC_API_KEY has a safe default in app/config.py.

ENVIRONMENT=production
# CORS only matters cross-origin. In production the SPA and the API share one domain
# (traefik routes /api to the app), so this is optional; set it to your domain to be safe.
CORS_ORIGINS=https://yourdomain.com

# Claude / Anthropic
# ------------------------------------------------------------------------------
ANTHROPIC_API_KEY=changeme
MODEL_LEGAL=claude-sonnet-4-6
MODEL_BANKING=claude-sonnet-4-6
MODEL_MENU=claude-opus-4-8

# French business registry (free, no auth) — non-blocking enrichment
# ------------------------------------------------------------------------------
REGISTRY_BASE_URL=https://recherche-entreprises.api.gouv.fr
REGISTRY_TIMEOUT_SECONDS=3

# Cost guardrail (EUR soft cap per onboarding; 0 disables)
# ------------------------------------------------------------------------------
COST_CAP_EUR=0.50

# Analytics (optional — empty key = no-op stub; events still go to the admin DB)
# ------------------------------------------------------------------------------
AMPLITUDE_API_KEY=
