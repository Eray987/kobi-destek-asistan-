"""Dense retrieval: embed chunks and queries, rank chunks by cosine similarity.

Kept deliberately small (NumPy, in memory) so every experiment's change is easy to
see. The embedding model is passed in as an object with an `encode` method, so the
tests can use a tiny fake model and never download anything.
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from kobi_asistan.retrieval.chunking import Chunk


class Embedder(Protocol):
    def embed_queries(self, texts: list[str]) -> np.ndarray: ...
    def embed_passages(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    """Wraps a sentence-transformers model.

    E5 models expect "query: " / "passage: " prefixes; other models get none.
    """

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # heavy import, only when used

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self._e5 = "e5" in model_name.lower()

    def _encode(self, texts: list[str], prefix: str) -> np.ndarray:
        if self._e5:
            texts = [prefix + t for t in texts]
        return self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)

    def embed_queries(self, texts: list[str]) -> np.ndarray:
        return self._encode(texts, "query: ")

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        return self._encode(texts, "passage: ")


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)


@dataclass
class Hit:
    chunk: Chunk
    score: float


class DenseIndex:
    def __init__(self, chunks: list[Chunk], embedder: Embedder):
        self.chunks = chunks
        self.embedder = embedder
        self.matrix = _normalize(np.asarray(embedder.embed_passages([c.text for c in chunks])))

    def search(self, query: str, k: int = 5) -> list[Hit]:
        q = _normalize(np.asarray(self.embedder.embed_queries([query])))[0]
        scores = self.matrix @ q  # cosine similarity, since both sides are unit length
        top = np.argsort(-scores)[:k]
        return [Hit(self.chunks[i], float(scores[i])) for i in top]
