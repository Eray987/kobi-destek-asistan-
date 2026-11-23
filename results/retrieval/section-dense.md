# Retrieval: section-dense

```json
{
  "name": "section-dense",
  "date": "2026-11-23 09:55 UTC",
  "testset": "questions_v0.jsonl",
  "questions_scored": 20,
  "retriever": "dense",
  "model": "intfloat/multilingual-e5-small",
  "chunking": "section_aware",
  "chunk_words": 200,
  "chunk_overlap": 30,
  "num_chunks": 109,
  "k": 5,
  "index_seconds": 1.02,
  "query_latency_ms_p50": 5.9,
  "query_latency_ms_p95": 7.4,
  "python": "3.15.0",
  "machine": "arm64"
}
```

| Group | n | Recall@5 (any) | Recall@5 (all) | MRR@5 |
|---|---|---|---|---|
| **overall** | 20 | 0.95 | 0.85 | 0.70 |
| colloquial | 2 | 0.50 | 0.50 | 0.10 |
| legislation | 1 | 1.00 | 1.00 | 0.25 |
| multi_evidence | 2 | 1.00 | 0.50 | 1.00 |
| prompt_injection | 1 | 1.00 | 1.00 | 0.33 |
| single_source | 14 | 1.00 | 0.93 | 0.80 |

## Questions with no gold section in the top 5 (1)

- **q011** (colloquial) kulaklik aldim paketini actim iade olurmu
  - gold: idefix-iade-kosullari#all, idefix-iade-ve-degisim#faq-87
  - retrieved: idefix-iade-ve-degisim::faq-94, idefix-sikca-sorulan-sorular::faq-46, idefix-sikca-sorulan-sorular::faq-47, idefix-odeme::faq-50, idefix-iade-ve-degisim::faq-101
