.DEFAULT_GOAL := help
COMPOSE_LOCAL := docker compose -f docker-compose.local.yml
COMPOSE_PROD  := docker compose -f docker-compose.production.yml

.PHONY: help up down logs build sh-app test test-live fmt deploy

help: ## List commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

up: ## Start local stack (postgres + app:8000 + web:5173)
	$(COMPOSE_LOCAL) up --build

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

fmt: ## Format/lint both sides
	$(COMPOSE_LOCAL) run --rm app sh -c "ruff check --fix . && ruff format ."

deploy: ## Build + (re)start the production stack (run on the server, env files in place)
	$(COMPOSE_PROD) up -d --build
