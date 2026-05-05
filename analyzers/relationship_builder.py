"""Create graph relationships from normalized records and extracted entities."""

from __future__ import annotations

import hashlib
from typing import Any


class RelationshipBuilder:
    """Translate records into graph nodes and edges."""

    def build(
        self,
        record: dict[str, Any],
        schema: dict[str, Any],
        entities: dict[str, Any],
        labels: dict[str, str],
    ) -> dict[str, list[dict[str, Any]]]:
        nodes: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []

        primary_label = labels["primary"]
        record_id = self._record_id(record, schema)
        title_field = schema.get("title_field")
        source_field = schema.get("source_field")
        query_field = schema.get("query_field")

        record_node = {
            "id": record_id,
            "label": primary_label,
            "properties": record,
        }
        nodes.append(record_node)

        source_value = record.get(source_field) if source_field else None
        if source_value:
            source_node_id = self._node_id(labels["source"], str(source_value))
            nodes.append(
                {
                    "id": source_node_id,
                    "label": labels["source"],
                    "properties": {"name": str(source_value)},
                }
            )
            relationships.append(
                {
                    "type": "PUBLISHED_BY",
                    "from": record_id,
                    "to": source_node_id,
                    "properties": {},
                }
            )

        query_value = record.get(query_field) if query_field else None
        if query_value:
            topic_node_id = self._node_id(labels["topic"], str(query_value))
            nodes.append(
                {
                    "id": topic_node_id,
                    "label": labels["topic"],
                    "properties": {"name": str(query_value)},
                }
            )
            relationships.append(
                {
                    "type": "TAGGED_WITH",
                    "from": record_id,
                    "to": topic_node_id,
                    "properties": {},
                }
            )

        for bucket, items in entities.items():
            if bucket == "sentiment":
                record_node["properties"]["sentiment"] = items
                continue
            for value in items:
                label = "Topic" if bucket == "key_topics" else labels["entity"]
                entity_node_id = self._node_id(label, value)
                nodes.append(
                    {
                        "id": entity_node_id,
                        "label": label,
                        "properties": {"name": value, "entity_type": bucket},
                    }
                )
                relationships.append(
                    {
                        "type": "MENTIONS",
                        "from": record_id,
                        "to": entity_node_id,
                        "properties": {"entity_type": bucket},
                    }
                )

        if title_field and record.get(title_field):
            keyword_nodes, keyword_relationships = self._infer_similarity_edges(
                record_id, record, title_field
            )
            nodes.extend(keyword_nodes)
            relationships.extend(keyword_relationships)

        return {"nodes": nodes, "relationships": relationships}

    @staticmethod
    def _record_id(record: dict[str, Any], schema: dict[str, Any]) -> str:
        field = schema.get("primary_id_field")
        raw = record.get(field) if field else None
        if raw:
            return f"{schema.get('primary_label', 'Record')}:{raw}"
        digest = hashlib.sha1(repr(sorted(record.items())).encode("utf-8")).hexdigest()
        return f"{schema.get('primary_label', 'Record')}:{digest}"

    @staticmethod
    def _node_id(label: str, value: str) -> str:
        return f"{label}:{value.strip()}"

    @staticmethod
    def _infer_similarity_edges(
        record_id: str, record: dict[str, Any], title_field: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        words = {
            token.lower().strip(".,:;!?()[]{}")
            for token in str(record.get(title_field, "")).split()
            if len(token) > 3
        }
        nodes = []
        relationships = []
        for token in sorted(words)[:5]:
            topic_id = f"Topic:{token}"
            nodes.append(
                {
                    "id": topic_id,
                    "label": "Topic",
                    "properties": {"name": token, "entity_type": "keyword"},
                }
            )
            relationships.append(
                {
                    "type": "HAS_KEYWORD",
                    "from": record_id,
                    "to": topic_id,
                    "properties": {"keyword": token},
                }
            )
        return nodes, relationships
