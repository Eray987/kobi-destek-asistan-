# Shortcuts for common commands. Example: make test
.PHONY: install db-up db-down db-check test format check

install:    ## Create the virtual environment and install dependencies
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

db-up:      ## Start PostgreSQL + pgvector with Docker
	docker compose up -d

db-down:    ## Stop the database
	docker compose down

db-check:   ## Try the database connection
	.venv/bin/python scripts/check_db.py

test:       ## Run the tests
	.venv/bin/pytest -v

format:     ## Auto-format the code
	.venv/bin/ruff format .
	.venv/bin/ruff check --fix .

check:      ## Run the same checks as CI, locally
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .
	.venv/bin/pytest -v
