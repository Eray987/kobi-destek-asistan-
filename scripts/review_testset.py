"""Prints every test-set question next to its evidence text, for hand verification.

    python scripts/review_testset.py              # questions not yet verified
    python scripts/review_testset.py --all        # every question
    python scripts/review_testset.py q007         # a single question

Run `make data` first. Exits with an error if an evidence ID is missing from the
downloaded documents (a typo in the test set or a changed source page).
"""

import sys
import textwrap
from pathlib import Path

from kobi_asistan.data.testset import load, load_sections, missing_evidence

ROOT = Path(__file__).resolve().parent.parent
TESTSET = ROOT / "data" / "testset" / "questions_v0.jsonl"
MAX_CHARS = 700


def main(args: list[str]) -> int:
    questions = load(TESTSET)
    sections = load_sections(ROOT / "data" / "raw", ROOT / "data" / "legislation")
    if not sections:
        print("No downloaded documents found. Run `make data` first.")
        return 1

    missing = missing_evidence(questions, sections)
    if missing:
        print("Evidence IDs not found in the downloaded documents:")
        print("\n".join(f"  {m}" for m in missing))
        return 1

    ids = [a for a in args if not a.startswith("--")]
    if ids:
        questions = [q for q in questions if q["id"] in ids]
    elif "--all" not in args:
        questions = [q for q in questions if not q["verified"]]

    for q in questions:
        print("=" * 80)
        print(f"{q['id']}  [{q['category']}, {q['difficulty']}]  answerable={q['answerable']}")
        print(f"Q: {q['question']}")
        print(f"Expected: {q['expected_answer']}")
        if not q["supporting_section_ids"]:
            print("Evidence: (none - check that the documents really do not answer this)")
        for item in q["supporting_section_ids"]:
            title, text = sections[item]
            if len(text) > MAX_CHARS:
                text = text[:MAX_CHARS] + " [...]"
            print(f"\n--- {item}: {title}")
            print(textwrap.indent(text, "    "))
        print()

    print(f"{len(questions)} question(s) shown. All evidence IDs exist.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
