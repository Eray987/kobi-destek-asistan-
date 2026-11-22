# Evaluation test set

`questions_v0.jsonl` is the first 25-question pilot set (one question per line). Questions are
written in **Turkish** on purpose: the project studies RAG for Turkish customer support. They are
based on the idefix help centre and the Distance Contracts Regulation (see `../sources.yaml`).

| Field | Meaning |
|---|---|
| `id` | Stable question ID |
| `store` | Store the question belongs to (every question belongs to exactly one store) |
| `question` | The customer's question (Turkish) |
| `category` | `single_source`, `multi_evidence`, `colloquial`, `legislation`, `unanswerable`, `prompt_injection`, `off_topic` |
| `difficulty` | `easy`, `medium`, `hard` |
| `answerable` | Do the documents contain the answer? |
| `expected_answer` | Reference answer, short, in our own words (Turkish) |
| `supporting_doc_ids` | Documents that contain the answer |
| `supporting_section_ids` | Sections that contain the answer, as `doc_id#section_id` (e.g. `idefix-odeme#faq-49`) |
| `verified` | Has a human checked this row against the source text? |

Rules (checked automatically on every `pytest` run):
- Unanswerable questions have empty evidence fields.
- Answerable questions have at least one evidence section.

**Important:** the questions were drafted with AI assistance, so every row starts as
`verified: false`. Check each row against the text in `data/raw/` and set it to `true` when it is
correct. Experiments must only use verified rows.

Section IDs stay stable even when the chunking strategy changes; chunk IDs will be mapped back to
these sections.
