"""Generate Cypher for nodes and relationships."""

from __future__ import annotations

import json
from typing import Any


def _cypher_map(d: dict[str, Any]) -> str:
    """Convert a dict to a Cypher map literal with unquoted keys."""
    pairs = ", ".join(f"{k}: {json.dumps(v, ensure_ascii=True)}" for k, v in d.items())
    return "{" + pairs + "}"


class QueryBuilder:
    """Build human-readable Cypher statements for graph import."""

    @staticmethod
    def node_merge(node: dict[str, Any]) -> str:
        props = _cypher_map(node["properties"])
        return (
            f"MERGE (n:{node['label']} {{id: {json.dumps(node['id'])}}}) "
            f"SET n += {props}"
        )

    @staticmethod
    def relationship_merge(relationship: dict[str, Any]) -> str:
        props = _cypher_map(relationship.get("properties", {}))
        return (
            f"MATCH (a {{id: {json.dumps(relationship['from'])}}}) "
            f"MATCH (b {{id: {json.dumps(relationship['to'])}}}) "
            f"MERGE (a)-[r:{relationship['type']}]->(b) "
            f"SET r += {props}"
        )
