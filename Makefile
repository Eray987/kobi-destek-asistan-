# Shortcuts for common commands. Example: make test
#
# The virtual environment is created automatically on first use.
# To pick a specific interpreter:  make install PYTHON=python3.12
.PHONY: install db-up db-down db-check data review eval experiments compare test format check

PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin
# Marker file: rebuilt whenever pyproject.toml (the dependency list) changes
STAMP := $(VENV)/.installed

install: $(STAMP)  ## Create the virtual environment and install dependencies

$(STAMP): pyproject.toml
	@$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null || { \
		echo "Error: Python 3.11+ is required, but '$(PYTHON)' is $$($(PYTHON) --version 2>&1)."; \
		echo "On macOS:  brew install python@3.12  then  make install PYTHON=python3.12"; \
		exit 1; }
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev,ml]"
	@test -f .env || { cp .env.example .env && echo "Created .env from .env.example"; }
	@touch $(STAMP)

db-up:             ## Start PostgreSQL + pgvector with Docker
	docker compose up -d --wait

db-down:           ## Stop the database
	docker compose down

db-check: $(STAMP)  ## Try the database connection
	$(BIN)/python scripts/check_db.py

data: $(STAMP)     ## Download the source pages and convert them to Markdown (data/sources.yaml)
	$(BIN)/python scripts/download_sources.py

review: $(STAMP)   ## Show unverified test-set questions next to their evidence
	$(BIN)/python scripts/review_testset.py

eval: $(STAMP)     ## Baseline retrieval experiment -> results/retrieval/
	$(BIN)/python scripts/evaluate_retrieval.py

experiments: $(STAMP)  ## Every chunking x retriever combination, then the comparison table
	for c in fixed section; do for r in dense bm25 hybrid; do \
		$(BIN)/python scripts/evaluate_retrieval.py --chunking $$c --retriever $$r > /dev/null || exit 1; \
		echo "done: $$c + $$r"; \
	done; done
	$(BIN)/python scripts/compare_results.py

compare: $(STAMP)  ## Comparison table of all saved runs
	$(BIN)/python scripts/compare_results.py

test: $(STAMP)     ## Run the tests
	$(BIN)/pytest -v

format: $(STAMP)   ## Auto-format the code
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

check: $(STAMP)    ## Run the same checks as CI, locally
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .
	$(BIN)/pytest -v
