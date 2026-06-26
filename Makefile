.DEFAULT_GOAL := help
COMPOSE_LOCAL := docker compose -f docker-compose.local.yml
COMPOSE_PROD  := docker compose -f docker-compose.production.yml

.PHONY: help up dev-backend down logs build sh-app test test-live seed fmt deploy

help: ## List commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

up: ## Start full local stack in Docker (postgres + app:8000 + web:5173)
	$(COMPOSE_LOCAL) up --build

dev-backend: ## Backend only in Docker (postgres + app:8000, autoreload); run the frontend with `npm run dev`
	$(COMPOSE_LOCAL) up -d postgres
	$(COMPOSE_LOCAL) up --build app

down: ## Stop local stack
	$(COMPOSE_LOCAL) down

logs: ## Tail local logs
	$(COMPOSE_LOCAL) logs -f

build: ## Build local images
	$(COMPOSE_LOCAL) build

sh-app: ## Shell into the app container
	$(COMPOSE_LOCAL) exec app sh

test: ## Run the deterministic backend suite (no API key needed)
	$(COMPOSE_LOCAL) run --rm app pytest

test-live: ## Run parsing against the real Claude API on the 6 sample menus (needs ANTHROPIC_API_KEY)
	$(COMPOSE_LOCAL) run --rm app pytest -m live

seed: ## Reset and fill the local DB with demo onboardings + events for the admin dashboard
	$(COMPOSE_LOCAL) run --rm app python -m scripts.seed_demo --reset

fmt: ## Format/lint both sides
	$(COMPOSE_LOCAL) run --rm app sh -c "ruff check --fix . && ruff format ."

deploy: ## Build + (re)start the production stack (run on the server, env files in place)
	$(COMPOSE_PROD) up -d --build
