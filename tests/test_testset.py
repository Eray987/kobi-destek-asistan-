from collections import Counter
from pathlib import Path

from kobi_asistan.data.testset import find_errors, load

TESTSET = Path(__file__).parent.parent / "data" / "testset" / "questions_v0.jsonl"


def test_testset_follows_the_rules():
    assert find_errors(load(TESTSET)) == []


def test_at_least_five_unanswerable_questions():
    assert sum(not q["answerable"] for q in load(TESTSET)) >= 5


def test_key_categories_are_represented():
    counts = Counter(q["category"] for q in load(TESTSET))
    for category in ["single_source", "unanswerable", "colloquial", "prompt_injection"]:
        assert counts[category] >= 1, f"no questions in category {category}"


def test_validator_catches_a_bad_row():
    bad = {
        "id": "x1",
        "store": "s",
        "question": "Soru?",
        "category": "unanswerable",
        "difficulty": "easy",
        "answerable": False,
        "expected_answer": "Yok.",
        "supporting_doc_ids": ["d"],
        "supporting_section_ids": ["d#b"],
        "verified": False,
    }
    assert any("must be empty" in e for e in find_errors([bad]))
