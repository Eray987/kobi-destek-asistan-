"""Prints one comparison table from every run in results/retrieval/.

    python scripts/compare_results.py              # all runs
    python scripts/compare_results.py --by-category

The table is Markdown, so it can be pasted into the report or a PR.
"""

import argparse
import json
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results" / "retrieval"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--by-category", action="store_true", help="one row per run and category")
    args = p.parse_args(argv)

    runs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(RESULTS.glob("*.json"))]
    if not runs:
        print("No results yet. Run `make eval` first.")
        return 1

    k = runs[0]["config"]["k"]
    group = "| Category " if args.by_category else ""
    print(f"| Run | Chunking | Retriever {group}| n | R@{k} any | R@{k} all | MRR@{k} | p50 ms |")
    print("|---|---|---|" + ("---|" if args.by_category else "") + "---|---|---|---|---|")
    for run in runs:
        c = run["config"]
        groups = run["by_category"].items() if args.by_category else [(None, run["overall"])]
        for category, s in groups:
            cells = [c["name"], c["chunking"], c["retriever"]]
            cells += [category] if args.by_category else []
            cells += [
                str(s["n"]),
                f"{s['recall_any']:.2f}",
                f"{s['recall_all']:.2f}",
                f"{s['mrr']:.2f}",
                str(c["query_latency_ms_p50"]),
            ]
            print("| " + " | ".join(cells) + " |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
