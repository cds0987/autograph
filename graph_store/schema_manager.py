"""Create simple constraints and indexes for the exported graph."""

from __future__ import annotations

from typing import Any


class SchemaManager:
    """Provide portable constraint statements for Neo4j import."""

    def build_constraints(self, labels: list[str]) -> list[str]:
        statements = []
        for label in sorted(set(labels)):
            statements.append(
                f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            )
        return statements
