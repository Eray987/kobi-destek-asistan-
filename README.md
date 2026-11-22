# KOBİ Support Assistant

A document-grounded customer support assistant for Turkish SMEs (KOBİ), built as a two-semester capstone project (2026–2027).

The assistant answers customer questions in Turkish **only from the company's own documents**, cites the source of every answer, and hands the customer over to a human agent instead of guessing when the documents don't contain the answer. The main research contribution is a Turkish evaluation set and controlled experiments comparing RAG design choices: chunking, hybrid search, reranking and abstention.

> 🇹🇷 Türkçe kurulum rehberi: [docs/KURULUM_TR.md](docs/KURULUM_TR.md)

## Roadmap

- [x] 1. Repository and engineering foundation
- [ ] 2. Source documents + 25-question hand-verified pilot test set
- [ ] 3. Baseline retrieval (dense vector search only), Recall@5 and MRR
- [ ] 4. LLM answers with citations + human hand-off, FastAPI `/ask` endpoint

## Project layout

```
src/kobi_asistan/     Application code
tests/                Automated tests (pytest)
scripts/              Helper scripts run by hand
data/                 Source list and evaluation set
docker/postgres/      SQL that runs when the database is first created
docs/                 Additional documentation
.github/workflows/    GitHub Actions (CI)
```

## Getting started (macOS / Linux)

Requirements: Python 3.11+, Git, [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone https://github.com/Eray987/kobi-destek-asistan-.git
cd kobi-destek-asistan-

cp .env.example .env     # create your local settings file
make install             # .venv virtual environment + dependencies
make db-up               # PostgreSQL + pgvector via Docker
make db-check            # should print "Connected"
make test                # all tests should pass
```

Every `make` target is a plain shell command in the [`Makefile`](Makefile) if you prefer to run it directly.

## Tech stack and why

| Tool | Purpose |
|---|---|
| **Python 3.11+** | Main language; the first RAG baseline is plain Python so every experiment's change stays visible |
| **PostgreSQL + pgvector** | Documents, versions and embeddings in one database, with vector similarity search |
| **Docker Compose** | Runs the database identically on any machine with one command |
| **pytest** | Unit and integration tests; also keeps experiments reproducible |
| **ruff** | Linting and formatting |
| **GitHub Actions** | Runs lint and tests (with a real pgvector service) on every push and PR |
| **`.env` + `.env.example`** | Keeps credentials out of the code and out of Git |

Deliberately **not** used yet: Kubernetes, LangChain/LlamaIndex, containerising the app itself (may come with the API step).

## Development workflow

```bash
git checkout main && git pull
git checkout -b my-feature
# ... write code ...
make format && make check
git commit -am "Describe what changed"
git push -u origin my-feature   # then open a pull request
```
