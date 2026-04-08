.DEFAULT_GOAL := help
VENV := .venv

# ── Bootstrap ────────────────────────────────────────────────────────────────

.PHONY: bootstrap
bootstrap: ## Create venv and install package with dev tools
	@./scripts/bootstrap.sh

# ── Quality ──────────────────────────────────────────────────────────────────

.PHONY: lint
lint: ## Run ruff linter and format check
	@test -d "$(VENV)" || { echo "No venv found. Run 'make bootstrap' first."; exit 1; }
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

.PHONY: format
format: ## Auto-fix lint issues and reformat code
	@test -d "$(VENV)" || { echo "No venv found. Run 'make bootstrap' first."; exit 1; }
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

.PHONY: test
test: ## Run the test suite
	@test -d "$(VENV)" || { echo "No venv found. Run 'make bootstrap' first."; exit 1; }
	$(VENV)/bin/pytest -q

.PHONY: coverage
coverage: ## Run tests with coverage report
	@test -d "$(VENV)" || { echo "No venv found. Run 'make bootstrap' first."; exit 1; }
	$(VENV)/bin/pytest --cov=hydradb_cli --cov-report=term-missing -q

# ── Utilities ────────────────────────────────────────────────────────────────

.PHONY: clean
clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
