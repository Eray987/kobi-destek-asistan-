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


def section_aware(
    documents: list[Document], max_words: int = 200, overlap: int = 30
) -> list[Chunk]:
    """One chunk per section (FAQ entry, legal article), so answers are never cut in two.

    A section longer than `max_words` is split into windows of `max_words` words
    with `overlap` shared. Every window starts with the section title, because a
    window from the middle of a long article would otherwise lose its topic.
    """
    if not 0 <= overlap < max_words:
        raise ValueError("overlap must be >= 0 and smaller than max_words")
    step = max_words - overlap
    chunks = []
    for doc in documents:
        for section in doc.sections:
            key = f"{doc.doc_id}#{section.id}"
            base_id = f"{doc.doc_id}::{section.id}"
            tokens = section.text.split()
            if len(tokens) <= max_words:
                windows = [tokens]
            else:
                windows = []
                for start in range(0, len(tokens), step):
                    windows.append(tokens[start : start + max_words])
                    if start + max_words >= len(tokens):
                        break
            for n, window in enumerate(windows):
                chunks.append(
                    Chunk(
                        chunk_id=base_id if len(windows) == 1 else f"{base_id}.{n}",
                        doc_id=doc.doc_id,
                        text=_section_text(section.title, " ".join(window)),
                        section_keys=(key,),
                    )
                )
    return chunks


STRATEGIES = {"fixed": fixed_size, "section": section_aware}
