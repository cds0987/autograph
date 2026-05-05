"""Tests for SchemaAnalyzer."""

from __future__ import annotations

from autograph.analyzers.schema_analyzer import SchemaAnalyzer
from autograph.core.config import GraphConfig


def _analyzer():
    return SchemaAnalyzer(GraphConfig())


class TestSchemaAnalyzer:
    def test_detects_id_field(self, sample_records):
        schema = _analyzer().analyze(sample_records)
        assert schema["primary_id_field"] == "id"

    def test_detects_title_field(self, sample_records):
        schema = _analyzer().analyze(sample_records)
        assert schema["title_field"] == "title"

    def test_detects_source_field(self, sample_records):
        schema = _analyzer().analyze(sample_records)
        assert schema["source_field"] == "source"

    def test_detects_query_field(self, sample_records):
        schema = _analyzer().analyze(sample_records)
        assert schema["query_field"] == "category"

    def test_primary_label_from_config(self, sample_records):
        schema = _analyzer().analyze(sample_records)
        assert schema["primary_label"] == "Record"

    def test_text_fields_populated(self, sample_records):
        schema = _analyzer().analyze(sample_records)
        assert "summary" in schema["text_fields"]

    def test_available_fields_lists_all_keys(self, sample_records):
        schema = _analyzer().analyze(sample_records)
        for key in sample_records[0]:
            assert key in schema["available_fields"]

    def test_node_types_present(self, sample_records):
        schema = _analyzer().analyze(sample_records)
        labels = [nt["label"] for nt in schema["node_types"]]
        assert "Record" in labels
        assert "Source" in labels
        assert "Entity" in labels

    def test_relationships_present(self, sample_records):
        schema = _analyzer().analyze(sample_records)
        types = [r["type"] for r in schema["relationships"]]
        assert "MENTIONS" in types
        assert "PUBLISHED_BY" in types
