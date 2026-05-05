"""Infer a graph schema from arbitrary tabular-like records."""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..core.config import GraphConfig


class SchemaAnalyzer:
    """Build a lightweight schema plan from sample records."""

    def __init__(self, config: GraphConfig) -> None:
        self.config = config

    def analyze(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        sample = records[: self.config.sample_size]
        keys = Counter()
        id_candidates = Counter()
        text_fields = Counter()
        category_fields = Counter()

        for record in sample:
            for key, value in record.items():
                keys[key] += 1
                lowered = key.lower()
                if lowered in {"id", "uuid", "url", "slug", "key"} or lowered.endswith("_id"):
                    id_candidates[key] += 3
                if isinstance(value, str):
                    if len(value.split()) >= 4:
                        text_fields[key] += 1
                    else:
                        category_fields[key] += 1

        primary_id = id_candidates.most_common(1)[0][0] if id_candidates else None
        title_field = self._first_matching_key(keys, {"title", "name", "headline", "subject"})
        source_field = self._first_matching_key(keys, {"source", "publisher", "author", "origin"})
        query_field = self._first_matching_key(keys, {"query", "topic", "category", "tag"})
        text_like_fields = [name for name, _ in text_fields.most_common(4)]

        return {
            "primary_label": self.config.article_label,
            "primary_id_field": primary_id or title_field or next(iter(keys), "id"),
            "title_field": title_field,
            "source_field": source_field,
            "query_field": query_field,
            "text_fields": text_like_fields,
            "available_fields": list(keys.keys()),
            "node_types": [
                {"label": self.config.article_label, "id_field": primary_id or title_field or "id"},
                {"label": self.config.source_label, "id_field": "name"},
                {"label": self.config.entity_label, "id_field": "name"},
                {"label": self.config.query_label, "id_field": "name"},
            ],
            "relationships": [
                {"type": "MENTIONS", "from": self.config.article_label, "to": self.config.entity_label},
                {"type": "PUBLISHED_BY", "from": self.config.article_label, "to": self.config.source_label},
                {"type": "TAGGED_WITH", "from": self.config.article_label, "to": self.config.query_label},
            ],
        }

    @staticmethod
    def _first_matching_key(counter: Counter[str], candidates: set[str]) -> str | None:
        for key, _ in counter.most_common():
            if key.lower() in candidates:
                return key
        return None
