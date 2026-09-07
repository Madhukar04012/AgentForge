"""A tiny in-memory vector store using cosine similarity over token-frequency vectors.

This is intentionally minimal — it exists so the framework can demonstrate retrieval
without pulling in numpy/faiss. Use a real vector DB in production.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from threading import RLock
from typing import Iterable

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _vectorize(tokens: Iterable[str]) -> dict[str, float]:
    counts = Counter(tokens)
    norm = math.sqrt(sum(c * c for c in counts.values()))
    if norm == 0:
        return {}
    return {tok: cnt / norm for tok, cnt in counts.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    # Iterate the smaller dict.
    small, big = (a, b) if len(a) <= len(b) else (b, a)
    return sum(val * big.get(tok, 0.0) for tok, val in small.items())


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._docs: dict[str, str] = {}
        self._vectors: dict[str, dict[str, float]] = {}
        self._lock = RLock()

    def add(self, doc_id: str, text: str) -> None:
        with self._lock:
            self._docs[doc_id] = text
            self._vectors[doc_id] = _vectorize(_tokenize(text))

    def delete(self, doc_id: str) -> None:
        with self._lock:
            self._docs.pop(doc_id, None)
            self._vectors.pop(doc_id, None)

    def search(self, query: str, k: int = 5) -> list[tuple[str, float]]:
        if k <= 0:
            return []
        qvec = _vectorize(_tokenize(query))
        with self._lock:
            scored = [(doc_id, _cosine(qvec, vec)) for doc_id, vec in self._vectors.items()]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def __len__(self) -> int:
        with self._lock:
            return len(self._docs)