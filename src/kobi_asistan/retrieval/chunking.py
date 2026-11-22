"""Splits documents into chunks for retrieval.

Every chunk remembers which sections (FAQ entries, legal articles) it overlaps.
That mapping is what lets us score retrieval against the test set's gold
evidence, which is recorded per section, whatever chunking strategy we use.
"""

from dataclasses import dataclass

from kobi_asistan.data.parsing import Document


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    section_keys: tuple[str, ...]  # "doc_id#section_id" values this chunk overlaps


def _section_text(title: str, text: str) -> str:
    # The section title (e.g. the FAQ question) carries a lot of meaning; keep it.
    return f"{title}\n{text}".strip() if title else text


def fixed_size(documents: list[Document], words: int = 120, overlap: int = 20) -> list[Chunk]:
    """Baseline: cuts each document into windows of `words` words, `overlap` shared.

    Section boundaries are ignored on purpose; respecting them is a separate
    experiment (section-aware chunking).
    """
    if not 0 <= overlap < words:
        raise ValueError("overlap must be >= 0 and smaller than words")
    step = words - overlap
    chunks = []
    for doc in documents:
        tokens: list[str] = []
        owners: list[str] = []  # owners[i] = section key of tokens[i]
        for section in doc.sections:
            section_tokens = _section_text(section.title, section.text).split()
            tokens.extend(section_tokens)
            owners.extend([f"{doc.doc_id}#{section.id}"] * len(section_tokens))

        start, n = 0, 0
        while start < len(tokens):
            end = min(start + words, len(tokens))
            keys = tuple(dict.fromkeys(owners[start:end]))  # unique, in order
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}::{n}",
                    doc_id=doc.doc_id,
                    text=" ".join(tokens[start:end]),
                    section_keys=keys,
                )
            )
            if end == len(tokens):
                break
            start += step
            n += 1
    return chunks
