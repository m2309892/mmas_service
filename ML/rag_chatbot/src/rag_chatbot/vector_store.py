"""In-memory vector store for the RAG prototype."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .documents import DocumentChunk


@dataclass(frozen=True)
class StoredChunk:
    chunk: DocumentChunk
    embedding: list[float]


@dataclass(frozen=True)
class SearchHit:
    chunk: DocumentChunk
    score: float


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding dimensions do not match")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._chunks: list[StoredChunk] = []

    def add_many(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")
        self._chunks.extend(
            StoredChunk(chunk=chunk, embedding=embedding)
            for chunk, embedding in zip(chunks, embeddings)
        )

    def search(self, query_embedding: list[float], *, top_k: int) -> list[SearchHit]:
        hits = [
            SearchHit(chunk=stored.chunk, score=cosine_similarity(query_embedding, stored.embedding))
            for stored in self._chunks
        ]
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:top_k]

    def __len__(self) -> int:
        return len(self._chunks)
