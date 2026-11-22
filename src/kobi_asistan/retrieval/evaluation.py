"""Retrieval metrics against the test set's gold evidence sections.

- Recall@k (any): at least one gold section appears in the top-k chunks.
- Recall@k (all): every gold section appears in the top-k chunks
  (differs from "any" only for multi-evidence questions).
- MRR: mean of 1 / rank of the first chunk that contains a gold section
  (0 if none in the top-k).

Only answerable questions are scored; unanswerable ones have no gold evidence and
belong to the abstention experiment.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from kobi_asistan.retrieval.dense import Hit


@dataclass
class QuestionResult:
    qid: str
    category: str
    question: str
    gold: list[str]
    retrieved: list[tuple[str, float, tuple[str, ...]]]  # (chunk_id, score, section_keys)
    first_hit_rank: int | None  # 1-based
    all_gold_found: bool


def score_question(q: dict, hits: list[Hit]) -> QuestionResult:
    gold = set(q["supporting_section_ids"])
    first = None
    found: set[str] = set()
    for rank, hit in enumerate(hits, start=1):
        overlap = gold.intersection(hit.chunk.section_keys)
        if overlap and first is None:
            first = rank
        found |= overlap
    return QuestionResult(
        qid=q["id"],
        category=q["category"],
        question=q["question"],
        gold=sorted(gold),
        retrieved=[(h.chunk.chunk_id, round(h.score, 4), h.chunk.section_keys) for h in hits],
        first_hit_rank=first,
        all_gold_found=found == gold,
    )


@dataclass
class Summary:
    n: int
    recall_any: float
    recall_all: float
    mrr: float


def summarize(results: list[QuestionResult]) -> Summary:
    n = len(results)
    if n == 0:
        return Summary(0, 0.0, 0.0, 0.0)
    return Summary(
        n=n,
        recall_any=sum(r.first_hit_rank is not None for r in results) / n,
        recall_all=sum(r.all_gold_found for r in results) / n,
        mrr=sum(1 / r.first_hit_rank for r in results if r.first_hit_rank) / n,
    )


@dataclass
class Report:
    overall: Summary
    by_category: dict[str, Summary] = field(default_factory=dict)
    failures: list[QuestionResult] = field(default_factory=list)


def build_report(results: list[QuestionResult]) -> Report:
    groups: dict[str, list[QuestionResult]] = defaultdict(list)
    for r in results:
        groups[r.category].append(r)
    return Report(
        overall=summarize(results),
        by_category={c: summarize(rs) for c, rs in sorted(groups.items())},
        failures=[r for r in results if r.first_hit_rank is None],
    )
