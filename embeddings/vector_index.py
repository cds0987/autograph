"""Simple in-memory vector index."""

from __future__ import annotations

from typing import Any

from .embedding_generator import EmbeddingGenerator


class VectorIndex:
    """Store vectors in memory for lightweight semantic search."""

    def __init__(self, generator: EmbeddingGenerator) -> None:
        self.generator = generator
        self._items: list[dict[str, Any]] = []

    def add(self, item_id: str, text: str, payload: dict[str, Any]) -> None:
        self._items.append(
            {
                "id": item_id,
                "text": text,
                "vector": self.generator.embed_text(text),
                "payload": payload,
            }
        )

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_vector = self.generator.embed_text(query)
        scored = []
        for item in self._items:
            score = self.generator.cosine_similarity(query_vector, item["vector"])
            scored.append({**item, "score": round(score, 4)})
        scored.sort(key=lambda entry: entry["score"], reverse=True)
        return scored[:limit]
