"""Tests for RelationshipBuilder."""

from __future__ import annotations

from autograph.analyzers.relationship_builder import RelationshipBuilder
from autograph.core.config import GraphConfig


def _labels():
    cfg = GraphConfig()
    return {
        "primary": cfg.article_label,
        "source": cfg.source_label,
        "entity": cfg.entity_label,
        "topic": cfg.query_label,
    }


def _schema():
    return {
        "primary_label": "Record",
        "primary_id_field": "id",
        "title_field": "title",
        "source_field": "source",
        "query_field": "category",
    }


def _entities():
    return {
        "organizations": ["Acme Corp"],
        "people": [],
        "locations": [],
        "technologies": ["AI"],
        "key_topics": ["healthcare"],
        "sentiment": "positive",
    }


class TestRelationshipBuilder:
    def setup_method(self):
        self.builder = RelationshipBuilder()
        self.record = {
            "id": "1",
            "title": "Acme launches AI",
            "source": "Acme News",
            "category": "healthcare",
            "summary": "AI helps doctors.",
        }

    def test_returns_nodes_and_relationships(self):
        result = self.builder.build(self.record, _schema(), _entities(), _labels())
        assert "nodes" in result
        assert "relationships" in result

    def test_primary_record_node_created(self):
        result = self.builder.build(self.record, _schema(), _entities(), _labels())
        labels = [n["label"] for n in result["nodes"]]
        assert "Record" in labels

    def test_source_node_created(self):
        result = self.builder.build(self.record, _schema(), _entities(), _labels())
        labels = [n["label"] for n in result["nodes"]]
        assert "Source" in labels

    def test_published_by_relationship_created(self):
        result = self.builder.build(self.record, _schema(), _entities(), _labels())
        types = [r["type"] for r in result["relationships"]]
        assert "PUBLISHED_BY" in types

    def test_tagged_with_relationship_created(self):
        result = self.builder.build(self.record, _schema(), _entities(), _labels())
        types = [r["type"] for r in result["relationships"]]
        assert "TAGGED_WITH" in types

    def test_mentions_relationship_for_entities(self):
        result = self.builder.build(self.record, _schema(), _entities(), _labels())
        types = [r["type"] for r in result["relationships"]]
        assert "MENTIONS" in types

    def test_sentiment_stored_on_record_node(self):
        result = self.builder.build(self.record, _schema(), _entities(), _labels())
        record_node = next(n for n in result["nodes"] if n["label"] == "Record")
        assert record_node["properties"]["sentiment"] == "positive"

    def test_keyword_nodes_created_from_title(self):
        result = self.builder.build(self.record, _schema(), _entities(), _labels())
        types = [r["type"] for r in result["relationships"]]
        assert "HAS_KEYWORD" in types

    def test_record_id_uses_primary_id_field(self):
        result = self.builder.build(self.record, _schema(), _entities(), _labels())
        ids = [n["id"] for n in result["nodes"]]
        assert any("1" in node_id for node_id in ids)

    def test_no_source_node_when_source_missing(self):
        record = {"id": "2", "title": "No source article", "category": "tech"}
        result = self.builder.build(record, _schema(), _entities(), _labels())
        labels = [n["label"] for n in result["nodes"]]
        assert "Source" not in labels
