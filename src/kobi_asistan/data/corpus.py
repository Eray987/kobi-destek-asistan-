"""Reads the Markdown documents written by `make data` back into `Document`s."""

import re
from pathlib import Path

from kobi_asistan.data.parsing import Document, Section

_SECTION_HEADING = re.compile(r"^## \[([^\]]+)\] ?(.*)$")
_TITLE = re.compile(r"^# (.*)$")


def read_document(path: Path) -> Document:
    doc = Document(doc_id=path.stem, title=path.stem)
    current: Section | None = None
    lines: list[str] = []

    def close() -> None:
        if current is not None:
            current.text = "\n".join(lines).strip()
            doc.sections.append(current)

    for line in path.read_text(encoding="utf-8").splitlines():
        heading = _SECTION_HEADING.match(line)
        if heading:
            close()
            current, lines = Section(heading.group(1), heading.group(2), ""), []
        elif current is not None:
            lines.append(line)
        elif title := _TITLE.match(line):
            doc.title = title.group(1)
    close()
    return doc


def load_documents(*folders: Path) -> list[Document]:
    """All documents under the given folders, sorted by path for reproducibility."""
    return [read_document(p) for folder in folders for p in sorted(folder.rglob("*.md"))]
