from collections import Counter
from pathlib import Path

import pytest

from kobi_asistan.data.testset import find_errors, load, load_sections, missing_evidence

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


def test_load_sections_reads_downloaded_markdown(tmp_path):
    (tmp_path / "shop-returns.md").write_text(
        "---\ndoc_id: shop-returns\n---\n\n# Returns\n\n"
        "## [faq-1] İade süresi?\n\n14 gün.\n\n## [faq-2] Kargo?\n\nÜcretsiz.\n",
        encoding="utf-8",
    )
    sections = load_sections(tmp_path)
    assert sections["shop-returns#faq-1"] == ("İade süresi?", "14 gün.")
    assert set(sections) == {"shop-returns#faq-1", "shop-returns#faq-2"}


DOWNLOADED = [TESTSET.parent.parent / "raw", TESTSET.parent.parent / "legislation"]


@pytest.mark.skipif(
    not (TESTSET.parent.parent / "raw").exists(), reason="sources not downloaded (make data)"
)
def test_every_evidence_id_exists_in_downloaded_documents():
    assert missing_evidence(load(TESTSET), load_sections(*DOWNLOADED)) == []
