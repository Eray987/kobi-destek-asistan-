"""Lexical retrieval (BM25) and hybrid fusion with dense search.

Turkish needs two tweaks before keyword matching works:

- Case and diacritics: customers often type without Turkish characters
  ("kulaklik aldim iade olurmu"), so both queries and chunks are lowercased with
  Turkish rules (I -> ı, İ -> i) and then folded to ASCII (ı -> i, ş -> s, ...).
- Suffixes: Turkish is agglutinative ("iade", "iadesi", "iadeler"), so every
  word is cut to its first `prefix` letters. Fixed-length prefix stemming is a
  simple, well-known baseline for Turkish IR (Can et al., 2008, JASIST).
"""

import math
import re
from collections import Counter
from typing import Protocol

from kobi_asistan.retrieval.chunking import Chunk
from kobi_asistan.retrieval.dense import Hit

_LOWER = str.maketrans({"I": "ı", "İ": "i"})
_FOLD = str.maketrans("çğıöşüâîû", "cgiosuaiu")
_WORD = re.compile(r"\w+")


def tokenize(text: str, prefix: int | None = 5) -> list[str]:
    """Turkish-aware lowercase, ASCII folding and optional prefix stemming."""
    text = text.translate(_LOWER).lower().translate(_FOLD)
    words = _WORD.findall(text)
    return [w[:prefix] for w in words] if prefix else words


class Retriever(Protocol):
    def search(self, query: str, k: int = 5) -> list[Hit]: ...


class BM25Index:
    """Okapi BM25 over chunks, in plain Python."""

    def __init__(
        self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75, prefix: int | None = 5
    ):
        self.chunks = chunks
        self.k1, self.b, self.prefix = k1, b, prefix
        self.term_freqs = [Counter(tokenize(c.text, prefix)) for c in chunks]
        self.lengths = [sum(tf.values()) for tf in self.term_freqs]
        self.avg_length = sum(self.lengths) / len(chunks) if chunks else 0.0
        doc_freq = Counter(term for tf in self.term_freqs for term in tf)
        n = len(chunks)
        self.idf = {t: math.log(1 + (n - df + 0.5) / (df + 0.5)) for t, df in doc_freq.items()}

    def scores(self, query: str) -> list[float]:
        terms = [t for t in dict.fromkeys(tokenize(query, self.prefix)) if t in self.idf]
        out = []
        for tf, length in zip(self.term_freqs, self.lengths, strict=True):
            norm = self.k1 * (1 - self.b + self.b * length / self.avg_length)
            out.append(
                sum(self.idf[t] * tf[t] * (self.k1 + 1) / (tf[t] + norm) for t in terms if t in tf)
            )
        return out

    def search(self, query: str, k: int = 5) -> list[Hit]:
        scores = self.scores(query)
        top = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [Hit(self.chunks[i], scores[i]) for i in top]


class HybridIndex:
    """Reciprocal Rank Fusion (Cormack et al., 2009) of several retrievers.

    Each retriever returns its top `depth` chunks; a chunk's fused score is the sum
    of 1 / (rrf_k + rank) over the lists it appears in. RRF uses only ranks, so the
    very different score scales of BM25 and cosine similarity don't matter.
    """

    def __init__(self, retrievers: list[Retriever], rrf_k: int = 60, depth: int = 50):
        self.retrievers = retrievers
        self.rrf_k, self.depth = rrf_k, depth

    def search(self, query: str, k: int = 5) -> list[Hit]:
        fused: dict[str, float] = {}
        chunks: dict[str, Chunk] = {}
        for retriever in self.retrievers:
            for rank, hit in enumerate(retriever.search(query, k=self.depth), start=1):
                cid = hit.chunk.chunk_id
                chunks[cid] = hit.chunk
                fused[cid] = fused.get(cid, 0.0) + 1 / (self.rrf_k + rank)
        top = sorted(fused, key=lambda cid: -fused[cid])[:k]
        return [Hit(chunks[cid], fused[cid]) for cid in top]
