# KOBİ Support Assistant

A document-grounded customer support assistant for Turkish SMEs (KOBİ), built as a two-semester capstone project (2026–2027).

The assistant answers customer questions in Turkish **only from the company's own documents**, cites the source of every answer, and hands the customer over to a human agent instead of guessing when the documents don't contain the answer. The main research contribution is a Turkish evaluation set and controlled experiments comparing RAG design choices: chunking, hybrid search, reranking and abstention.

> 🇹🇷 Türkçe kurulum rehberi: [docs/KURULUM_TR.md](docs/KURULUM_TR.md)

## Roadmap

- [x] 1. Repository and engineering foundation
- [x] 2. Real-world source documents (source list + download script) + 25-question pilot test set
  - [x] Hand-verify all 25 questions (`verified: true`)
- [ ] 3. Baseline retrieval (dense vector search only), Recall@5 and MRR
  - [x] Fixed-size chunking, dense search, evaluation script (`make eval`)
  - [x] First baseline results committed to `results/retrieval/`
  - [x] Section-aware chunking (`--chunking section`)
  - [ ] Chunking comparison results
  - [x] BM25 and hybrid search (`--retriever bm25|hybrid`, `make experiments`)
  - [ ] Retriever comparison results
- [ ] 4. LLM answers with citations + human hand-off, FastAPI `/ask` endpoint

## Project layout

```
src/kobi_asistan/     Application code
  data/               Source parsing, corpus loading and test-set validation
  retrieval/          Chunking, dense search and retrieval metrics
tests/                Automated tests (pytest)
scripts/              Helper scripts run by hand
data/                 Source list, legislation texts and the evaluation set
docker/postgres/      SQL that runs when the database is first created
docs/                 Additional documentation
.github/workflows/    GitHub Actions (CI)
```

## Getting started (macOS / Linux)

Requirements: Python 3.11+, Git, [Docker Desktop](https://www.docker.com/products/docker-desktop/).
macOS ships an older Python; install a newer one with `brew install python@3.12` and pass it as `make install PYTHON=python3.12`.

```bash
git clone https://github.com/Eray987/kobi-destek-asistan-.git
cd kobi-destek-asistan-

make install             # .venv + dependencies + .env (add PYTHON=python3.12 if needed)
make db-up               # PostgreSQL + pgvector via Docker
make db-check            # should print "Connected"
make data                # download the source documents
make test                # all tests should pass
```

Any target creates the virtual environment automatically if it is missing. Every `make` target is a plain shell command in the [`Makefile`](Makefile) if you prefer to run it directly.

## Data

Documents come from a real Turkish e-commerce help centre and from the Turkish Distance Contracts Regulation (*Mesafeli Sözleşmeler Yönetmeliği*). Company texts are copyrighted by the company, so they are **not committed**: the repository only holds the source list ([`data/sources.yaml`](data/sources.yaml)) and the download script.

- `make data` downloads every source, respecting `robots.txt` and pausing between requests.
- Company pages land in `data/raw/<store>/*.md` (gitignored); legislation lands in `data/legislation/*.md` (official text, freely reproducible under Turkish copyright law, FSEK art. 31).
- Each document starts with its source URL and access date. Every FAQ entry and every legal article is a section with a stable ID (`faq-64`, `article-12`), which the test set points to as evidence.
- Evaluation set: [`data/testset/`](data/testset/). Questions are in Turkish by design.

## Experiments

`make eval` runs the baseline retrieval experiment: fixed-size chunks (120 words, 20 overlap),
`intfloat/multilingual-e5-small` embeddings, cosine top-5 search in NumPy. It scores every
verified answerable question against its gold evidence sections and writes
`results/retrieval/<name>.json` and `.md`:

- **Recall@k (any)**: at least one gold section in the top k chunks
- **Recall@k (all)**: every gold section in the top k (matters for multi-evidence questions)
- **MRR@k**: mean of 1 / rank of the first chunk containing a gold section
- p50/p95 query latency, plus a list of failed questions for error analysis

Experiment 2 compares chunking strategies with the same model and k:

```bash
make eval                                                     # fixed-size baseline
.venv/bin/python scripts/evaluate_retrieval.py --chunking section   # one chunk per FAQ / article
```

Section-aware chunking keeps every FAQ entry and legal article in its own chunk (title + text);
a section longer than 200 words is split into 200-word windows (30 overlap) that each repeat the title.

Experiment 3 compares retrievers. `--retriever bm25` is keyword search (Okapi BM25) with Turkish-aware
lowercasing, ASCII folding (customers often type `iade olurmu` without Turkish letters) and
5-letter prefix stemming for suffixes. `--retriever hybrid` runs dense and BM25 and fuses the two
rankings with Reciprocal Rank Fusion. `make experiments` runs every chunking x retriever pair, and
`make compare` prints one table of all saved runs.

Options: `.venv/bin/python scripts/evaluate_retrieval.py --help` (chunking, retriever, chunk size, overlap, k, model, run name).
Result files contain only chunk and section IDs, never company text, so they are safe to commit.

## Tech stack and why

| Tool | Purpose |
|---|---|
| **Python 3.11+** | Main language; the first RAG baseline is plain Python so every experiment's change stays visible |
| **sentence-transformers + NumPy** | Multilingual embeddings and in-memory cosine search for the baseline (installed via the `ml` extra) |
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
