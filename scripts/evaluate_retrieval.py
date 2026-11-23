"""Retrieval experiment: chunking strategy + retriever (dense, BM25 or hybrid), top-k.

    python scripts/evaluate_retrieval.py                       # defaults below
    python scripts/evaluate_retrieval.py --words 80 --overlap 10 --name small-chunks
    python scripts/evaluate_retrieval.py --chunking section    # one chunk per FAQ / article
    python scripts/evaluate_retrieval.py --chunking section --retriever hybrid

Writes results/retrieval/<name>.json (config, metrics, per-question ranks) and
results/retrieval/<name>.md (tables + failed questions). Only chunk IDs are saved,
never the company text itself, so result files are safe to commit.
"""

import argparse
import json
import platform
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from kobi_asistan.data.corpus import load_documents
from kobi_asistan.data.testset import load
from kobi_asistan.retrieval.chunking import STRATEGIES
from kobi_asistan.retrieval.dense import DenseIndex, SentenceTransformerEmbedder
from kobi_asistan.retrieval.evaluation import Report, build_report, score_question
from kobi_asistan.retrieval.lexical import BM25Index, HybridIndex

ROOT = Path(__file__).resolve().parent.parent
TESTSET = ROOT / "data" / "testset" / "questions_v0.jsonl"
OUT_DIR = ROOT / "results" / "retrieval"
DEFAULTS = {
    "fixed": {"words": 120, "overlap": 20, "name": "baseline"},
    "section": {"words": 200, "overlap": 30, "name": "section"},
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--model", default="intfloat/multilingual-e5-small")
    p.add_argument(
        "--chunking",
        choices=sorted(STRATEGIES),
        default="fixed",
        help="fixed: word windows across the document (baseline)\n"
        "section: one chunk per FAQ entry / article, long ones split",
    )
    p.add_argument(
        "--words",
        type=int,
        help="chunk size in words (fixed) or max section size before splitting (section);\n"
        "default: 120 for fixed, 200 for section",
    )
    p.add_argument(
        "--overlap",
        type=int,
        help="words shared by neighbouring windows; default: 20 for fixed, 30 for section",
    )
    p.add_argument(
        "--retriever",
        choices=["dense", "bm25", "hybrid"],
        default="dense",
        help="dense: embedding cosine search; bm25: keyword search;\n"
        "hybrid: both, fused with Reciprocal Rank Fusion",
    )
    p.add_argument("--k", type=int, default=5, help="number of chunks retrieved per question")
    p.add_argument(
        "--name", help="name of the result files; default: <baseline|section>-<retriever>"
    )
    p.add_argument(
        "--include-unverified", action="store_true", help="also score unverified questions"
    )
    args = p.parse_args(argv)
    defaults = DEFAULTS[args.chunking]
    args.words = args.words if args.words is not None else defaults["words"]
    args.overlap = args.overlap if args.overlap is not None else defaults["overlap"]
    args.name = args.name or f"{defaults['name']}-{args.retriever}"
    return args


def to_markdown(report: Report, config: dict) -> str:
    def row(label: str, s) -> str:
        return f"| {label} | {s.n} | {s.recall_any:.2f} | {s.recall_all:.2f} | {s.mrr:.2f} |"

    k = config["k"]
    lines = [
        f"# Retrieval: {config['name']}",
        "",
        "```json",
        json.dumps(config, indent=2, ensure_ascii=False),
        "```",
        "",
        f"| Group | n | Recall@{k} (any) | Recall@{k} (all) | MRR@{k} |",
        "|---|---|---|---|---|",
        row("**overall**", report.overall),
        *[row(c, s) for c, s in report.by_category.items()],
        "",
        f"## Questions with no gold section in the top {k} ({len(report.failures)})",
        "",
    ]
    for f in report.failures:
        lines += [
            f"- **{f.qid}** ({f.category}) {f.question}",
            f"  - gold: {', '.join(f.gold)}",
            f"  - retrieved: {', '.join(cid for cid, _, _ in f.retrieved)}",
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    documents = load_documents(ROOT / "data" / "raw", ROOT / "data" / "legislation")
    if not documents:
        print("No downloaded documents found. Run `make data` first.")
        return 1

    questions = [
        q
        for q in load(TESTSET)
        if q["answerable"]
        and q["supporting_section_ids"]
        and (q["verified"] or args.include_unverified)
    ]
    chunk = STRATEGIES[args.chunking]
    if args.chunking == "fixed":
        chunks = chunk(documents, words=args.words, overlap=args.overlap)
    else:
        chunks = chunk(documents, max_words=args.words, overlap=args.overlap)
    print(f"{len(documents)} documents -> {len(chunks)} chunks; {len(questions)} questions")

    embedder = None
    if args.retriever != "bm25":
        print(f"Loading {args.model} (first run downloads it)...")
        embedder = SentenceTransformerEmbedder(args.model)

    t0 = time.perf_counter()
    if args.retriever == "dense":
        index = DenseIndex(chunks, embedder)
    elif args.retriever == "bm25":
        index = BM25Index(chunks)
    else:
        index = HybridIndex([DenseIndex(chunks, embedder), BM25Index(chunks)])
    index_seconds = time.perf_counter() - t0

    results, latencies = [], []
    for q in questions:
        t = time.perf_counter()
        hits = index.search(q["question"], k=args.k)
        latencies.append((time.perf_counter() - t) * 1000)
        results.append(score_question(q, hits))
    report = build_report(results)

    config = {
        "name": args.name,
        "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "testset": TESTSET.name,
        "questions_scored": len(questions),
        "retriever": args.retriever,
        "model": args.model if embedder else None,
        "chunking": chunk.__name__,
        "chunk_words": args.words,
        "chunk_overlap": args.overlap,
        "num_chunks": len(chunks),
        "k": args.k,
        "index_seconds": round(index_seconds, 2),
        "query_latency_ms_p50": round(float(np.percentile(latencies, 50)), 1),
        "query_latency_ms_p95": round(float(np.percentile(latencies, 95)), 1),
        "python": platform.python_version(),
        "machine": platform.machine(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "config": config,
        "overall": asdict(report.overall),
        "by_category": {c: asdict(s) for c, s in report.by_category.items()},
        "questions": [asdict(r) for r in results],
    }
    (OUT_DIR / f"{args.name}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    md = to_markdown(report, config)
    (OUT_DIR / f"{args.name}.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"Saved results/retrieval/{args.name}.json and .md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
