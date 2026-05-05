"""Tests for the GraphBuilder public API."""

from __future__ import annotations

from autograph import GraphBuilder


def make_builder():
    return GraphBuilder(use_embeddings=True, embedding_provider="local")


class TestGraphBuilder:
    def test_load_data_returns_self(self, sample_records):
        builder = make_builder()
        result = builder.load_data(sample_records)
        assert result is builder

    def test_build_graph_returns_graph(self, sample_records):
        graph = make_builder().load_data(sample_records).build_graph()
        assert "nodes" in graph
        assert "relationships" in graph

    def test_graph_has_nodes(self, sample_records):
        graph = make_builder().load_data(sample_records).build_graph()
        assert len(graph["nodes"]) > 0

    def test_graph_summary_record_count(self, sample_records):
        builder = make_builder().load_data(sample_records)
        builder.build_graph()
        summary = builder.graph_summary()
        assert summary["records"] == 2

    def test_graph_summary_has_node_labels(self, sample_records):
        builder = make_builder().load_data(sample_records)
        builder.build_graph()
        assert "Record" in builder.graph_summary()["node_labels"]

    def test_search_returns_results(self, sample_records):
        builder = make_builder().load_data(sample_records)
        builder.build_graph()
        results = builder.search("robotics", limit=1)
        assert len(results) >= 1

    def test_export_cypher_contains_merge(self, sample_records):
        builder = make_builder().load_data(sample_records)
        builder.build_graph()
        cypher = builder.export_cypher()
        assert "MERGE" in cypher

    def test_export_json(self, sample_records, tmp_path):
        builder = make_builder().load_data(sample_records)
        builder.build_graph()
        path = builder.export_json(tmp_path / "graph.json")
        assert path.exists()

    def test_load_from_csv_file(self, csv_path):
        builder = make_builder().load_data(csv_path)
        builder.build_graph()
        assert builder.graph_summary()["records"] > 0

    def test_load_from_json_file(self, json_path):
        builder = make_builder().load_data(json_path)
        builder.build_graph()
        assert builder.graph_summary()["records"] > 0

    def test_load_from_jsonl_file(self, jsonl_path):
        builder = make_builder().load_data(jsonl_path)
        builder.build_graph()
        assert builder.graph_summary()["records"] > 0
