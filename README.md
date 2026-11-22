# KOBİ Support Assistant

A document-grounded customer support assistant for Turkish SMEs (KOBİ), built as a two-semester capstone project (2026–2027).

The assistant answers customer questions in Turkish **only from the company's own documents**, cites the source of every answer, and hands the customer over to a human agent instead of guessing when the documents don't contain the answer. The main research contribution is a Turkish evaluation set and controlled experiments comparing RAG design choices: chunking, hybrid search, reranking and abstention.

> 🇹🇷 Türkçe kurulum rehberi: [docs/KURULUM_TR.md](docs/KURULUM_TR.md)

## Roadmap

- [x] 1. Repository and engineering foundation
- [x] 2. Real-world source documents (source list + download script) + 25-question pilot test set
  - [ ] Hand-verify all 25 questions (`verified: true`)
- [ ] 3. Baseline retrieval (dense vector search only), Recall@5 and MRR
- [ ] 4. LLM answers with citations + human hand-off, FastAPI `/ask` endpoint

## Project layout

```
src/kobi_asistan/     Application code
  data/               Source parsing and test-set validation
tests/                Automated tests (pytest)
scripts/              Helper scripts run by hand
data/                 Source list, legislation texts and the evaluation set
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
make data                # download the source documents
make test                # all tests should pass
```

Every `make` target is a plain shell command in the [`Makefile`](Makefile) if you prefer to run it directly.

## Data

Documents come from a real Turkish e-commerce help centre and from the Turkish Distance Contracts Regulation (*Mesafeli Sözleşmeler Yönetmeliği*). Company texts are copyrighted by the company, so they are **not committed**: the repository only holds the source list ([`data/sources.yaml`](data/sources.yaml)) and the download script.

- `make data` downloads every source, respecting `robots.txt` and pausing between requests.
- Company pages land in `data/raw/<store>/*.md` (gitignored); legislation lands in `data/legislation/*.md` (official text, freely reproducible under Turkish copyright law, FSEK art. 31).
- Each document starts with its source URL and access date. Every FAQ entry and every legal article is a section with a stable ID (`faq-64`, `article-12`), which the test set points to as evidence.
- Evaluation set: [`data/testset/`](data/testset/). Questions are in Turkish by design.

## Tech stack and why

| Tool | Purpose |
|---|---|
| **Python 3.11+** | Main language; the first RAG baseline is plain Python so every experiment's change stays visible |
| **PostgreSQL + pgvector** | Documents, versions and embeddings in one database, with vector similarity search |
| **Docker Compose** | Runs the database identically on any machine with one command |
| **pytest** | Unit and integration tests; also validates the evaluation set on every run |
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
