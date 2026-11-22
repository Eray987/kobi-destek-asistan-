"""Loading and validating the evaluation test set (JSONL).

Mistakes in a test set silently corrupt experiment results, so every row is checked
against these rules; the checks run on every `pytest` run.
"""

import json
import re
from pathlib import Path

CATEGORIES = {
    "single_source",  # the answer is in one section
    "multi_evidence",  # the answer needs more than one section
    "colloquial",  # everyday language, typos, missing Turkish characters
    "legislation",  # the answer is in a law/regulation
    "unanswerable",  # the documents don't contain the answer -> hand off to a human
    "prompt_injection",  # attempts to override the assistant's instructions
    "off_topic",  # unrelated to the store
}
DIFFICULTIES = {"easy", "medium", "hard"}
FIELDS = {
    "id",
    "store",
    "question",
    "category",
    "difficulty",
    "answerable",
    "expected_answer",
    "supporting_doc_ids",
    "supporting_section_ids",
    "verified",
}


def load(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no} is not valid JSON: {exc}") from exc
    return rows


def find_errors(questions: list[dict]) -> list[str]:
    """Returns a readable message for every row that breaks a rule."""
    errors = []
    seen = set()
    for q in questions:
        qid = q.get("id", "?")
        if set(q) != FIELDS:
            errors.append(f"{qid}: wrong fields, missing={FIELDS - set(q)} extra={set(q) - FIELDS}")
            continue
        if qid in seen:
            errors.append(f"{qid}: duplicate id")
        seen.add(qid)
        if q["category"] not in CATEGORIES:
            errors.append(f"{qid}: unknown category {q['category']!r}")
        if q["difficulty"] not in DIFFICULTIES:
            errors.append(f"{qid}: unknown difficulty {q['difficulty']!r}")
        if not q["question"].strip() or not q["expected_answer"].strip():
            errors.append(f"{qid}: empty question or expected answer")

        evidence = q["supporting_section_ids"]
        if q["answerable"]:
            if not evidence:
                errors.append(f"{qid}: answerable question has no evidence section")
        elif evidence or q["supporting_doc_ids"]:
            errors.append(f"{qid}: evidence fields must be empty for unanswerable questions")

        for item in evidence:
            if "#" not in item:
                errors.append(f"{qid}: evidence '{item}' is not in 'doc_id#section_id' format")
            elif item.split("#")[0] not in q["supporting_doc_ids"]:
                errors.append(f"{qid}: evidence '{item}' is not listed in supporting_doc_ids")
    return errors


_SECTION_HEADING = re.compile(r"^## \[([^\]]+)\] ?(.*)$")


def load_sections(*folders: Path) -> dict[str, tuple[str, str]]:
    """Reads the downloaded Markdown documents into {"doc_id#section_id": (title, text)}."""
    sections: dict[str, tuple[str, str]] = {}
    for folder in folders:
        for path in sorted(folder.rglob("*.md")):
            doc_id = path.stem
            key, title, lines = None, "", []
            for line in path.read_text(encoding="utf-8").splitlines():
                match = _SECTION_HEADING.match(line)
                if match:
                    if key:
                        sections[key] = (title, "\n".join(lines).strip())
                    key, title, lines = f"{doc_id}#{match.group(1)}", match.group(2), []
                elif key:
                    lines.append(line)
            if key:
                sections[key] = (title, "\n".join(lines).strip())
    return sections


def missing_evidence(questions: list[dict], sections: dict[str, tuple[str, str]]) -> list[str]:
    """Evidence IDs that do not exist in the downloaded documents."""
    return [
        f"{q['id']}: {item}"
        for q in questions
        for item in q["supporting_section_ids"]
        if item not in sections
    ]
