"""Tests for QueryBuilder and SchemaManager."""

from __future__ import annotations

from autograph.graph_store.query_builder import QueryBuilder
from autograph.graph_store.schema_manager import SchemaManager


class TestQueryBuilder:
    def test_node_merge_contains_label(self):
        node = {"id": "Record:1", "label": "Record", "properties": {"name": "Test"}}
        cypher = QueryBuilder.node_merge(node)
        assert "MERGE" in cypher
        assert "Record" in cypher

    def test_node_merge_uses_unquoted_keys(self):
        node = {"id": "Record:1", "label": "Record", "properties": {"title": "Hello"}}
        cypher = QueryBuilder.node_merge(node)
        assert "title:" in cypher or "title :" in cypher

    def test_relationship_merge_contains_type(self):
        rel = {
            "type": "PUBLISHED_BY",
            "from": "Record:1",
            "to": "Source:Acme",
            "properties": {},
        }
        cypher = QueryBuilder.relationship_merge(rel)
        assert "PUBLISHED_BY" in cypher

    def test_relationship_merge_has_match_and_merge(self):
        rel = {
            "type": "MENTIONS",
            "from": "Record:1",
            "to": "Entity:AI",
            "properties": {"entity_type": "technologies"},
        }
        cypher = QueryBuilder.relationship_merge(rel)
        assert cypher.count("MATCH") == 2
        assert "MERGE" in cypher


class TestSchemaManager:
    def test_builds_constraints_for_labels(self):
        statements = SchemaManager().build_constraints(["Record", "Source"])
        assert any("Record" in s for s in statements)
        assert any("Source" in s for s in statements)

    def test_deduplicates_labels(self):
        statements = SchemaManager().build_constraints(["Record", "Record"])
        assert len(statements) == 1

    def test_constraint_syntax(self):
        statements = SchemaManager().build_constraints(["Entity"])
        assert "REQUIRE" in statements[0]
        assert "IS UNIQUE" in statements[0]
