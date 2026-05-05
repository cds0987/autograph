"""Full integration test using data/ai_articles.csv."""

from __future__ import annotations

from autograph import GraphBuilder


def make_builder(csv_path):
    return (
        GraphBuilder(use_embeddings=True, embedding_provider="local")
        .load_data(csv_path)
    )


class TestFinalCSV:
    def test_records_loaded(self, csv_path):
        builder = make_builder(csv_path)
        builder.build_graph()
        assert builder.graph_summary()["records"] > 0

    def test_nodes_created(self, csv_path):
        builder = make_builder(csv_path)
        builder.build_graph()
        assert builder.graph_summary()["nodes"] > 0

    def test_relationships_created(self, csv_path):
        builder = make_builder(csv_path)
        builder.build_graph()
        assert builder.graph_summary()["relationships"] > 0

    def test_record_label_present(self, csv_path):
        builder = make_builder(csv_path)
        builder.build_graph()
        assert "Record" in builder.graph_summary()["node_labels"]

    def test_source_label_present(self, csv_path):
        builder = make_builder(csv_path)
        builder.build_graph()
        assert "Source" in builder.graph_summary()["node_labels"]

    def test_published_by_relationship_present(self, csv_path):
        builder = make_builder(csv_path)
        builder.build_graph()
        assert "PUBLISHED_BY" in builder.graph_summary()["relationship_types"]

    def test_search_returns_results(self, csv_path):
        builder = make_builder(csv_path)
        builder.build_graph()
        results = builder.search("artificial intelligence", limit=3)
        assert len(results) > 0

    def test_export_cypher_non_empty(self, csv_path):
        builder = make_builder(csv_path)
        builder.build_graph()
        assert len(builder.export_cypher()) > 0

    def test_export_json_file_created(self, csv_path, tmp_path):
        builder = make_builder(csv_path)
        builder.build_graph()
        path = builder.export_json(tmp_path / "graph_csv.json")
        assert path.exists()
        assert path.stat().st_size > 0
