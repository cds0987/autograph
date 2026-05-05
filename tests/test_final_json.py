"""
Live integration test: fetch AI articles -> build graph -> verify Neo4j.

This suite fetches a configurable number of fresh AI news articles using the
helper in tests/fetch_ai_articles.py, writes them to a temporary JSON file, and
then runs the full GraphBuilder pipeline with OpenAI + Neo4j.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

import pytest
import structlog
from dotenv import load_dotenv

from autograph import GraphBuilder


structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
        if os.getenv("SUP_ENV") == "dev"
        else structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger()


_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV)

NEO4J_URI = os.getenv("neoj4_url") or os.getenv("neo4j_url")
NEO4J_USER = os.getenv("neoj4_user") or os.getenv("neo4j_user", "neo4j")
NEO4J_PASSWORD = os.getenv("neoj4_password") or os.getenv("neo4j_password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
FETCH_LIMIT = max(1, int(os.getenv("AI_ARTICLES_LIMIT", "25")))

_neo4j_missing = not (NEO4J_URI and NEO4J_PASSWORD)
_openai_missing = not OPENAI_API_KEY


def _load_fetch_module() -> Any:
    module_path = Path(__file__).with_name("fetch_ai_articles.py")
    spec = importlib.util.spec_from_file_location("test_fetch_ai_articles_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load fetch helper from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fetched_dataset(tmp_path_factory) -> dict[str, Any]:
    fetch_module = _load_fetch_module()
    output_dir = tmp_path_factory.mktemp("ai_articles_live")

    log.info("phase.start", phase="fetch_articles", limit=FETCH_LIMIT)
    try:
        articles = fetch_module.fetch_articles(limit=FETCH_LIMIT)
    except Exception as exc:  # pragma: no cover - external network dependency
        pytest.skip(f"Unable to fetch AI articles: {exc}")

    if not articles:
        pytest.skip("Fetch returned 0 AI articles")

    fetch_module.write_outputs(articles, output_dir)

    metadata = {
        "articles": articles,
        "json_path": output_dir / "ai_articles.json",
        "expected_records": len(articles),
        "expected_sources": sum(1 for article in articles if article.get("source")),
        "expected_queries": sum(1 for article in articles if article.get("query")),
    }
    log.info(
        "phase.done",
        phase="fetch_articles",
        records=metadata["expected_records"],
        json_path=str(metadata["json_path"]),
    )
    return metadata


@pytest.fixture(scope="module")
def built_graph(fetched_dataset):
    """
    Phase 1 - load fetched JSON
    Phase 2 - build graph with LLM + embeddings
    Phase 3 - push to Neo4j with reset
    """
    if _openai_missing:
        pytest.skip("OPENAI_API_KEY not configured")
    if _neo4j_missing:
        pytest.skip("Neo4j env vars not configured")

    json_path = fetched_dataset["json_path"]
    log.info("phase.start", phase="load", source=str(json_path))
    builder = GraphBuilder(
        llm_api_key=OPENAI_API_KEY,
        llm_provider="openai",
        llm_model=OPENAI_MODEL,
        use_llm=True,
        use_embeddings=True,
        embedding_provider="openai",
        embedding_model=EMBEDDING_MODEL,
        neo4j_uri=NEO4J_URI,
        neo4j_password=NEO4J_PASSWORD,
        reset_database=True,
    )
    builder.config.neo4j_username = NEO4J_USER
    builder.load_data(json_path)
    log.info("phase.done", phase="load", records=len(builder.records))

    log.info(
        "phase.start",
        phase="build_graph",
        llm_model=OPENAI_MODEL,
        embedding_model=EMBEDDING_MODEL,
    )
    builder.build_graph()
    summary = builder.graph_summary()
    log.info(
        "phase.done",
        phase="build_graph",
        nodes=summary["nodes"],
        relationships=summary["relationships"],
        node_labels=summary["node_labels"],
        relationship_types=summary["relationship_types"],
    )

    log.info("phase.start", phase="push_neo4j", uri=NEO4J_URI, reset=True)
    builder.push_to_neo4j()
    log.info("phase.done", phase="push_neo4j")

    return {"builder": builder, "dataset": fetched_dataset}


@pytest.fixture(scope="module")
def neo4j_session(built_graph):
    log.info("phase.start", phase="neo4j_verify", uri=NEO4J_URI)
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        yield session
    driver.close()
    log.info("phase.done", phase="neo4j_verify")


class TestLLMGraphInMemory:
    def test_records_loaded(self, built_graph):
        builder = built_graph["builder"]
        expected = built_graph["dataset"]["expected_records"]
        count = builder.graph_summary()["records"]
        log.info("check", test="records_loaded", count=count, expected=expected)
        assert count == expected

    def test_nodes_created(self, built_graph):
        builder = built_graph["builder"]
        records = built_graph["dataset"]["expected_records"]
        count = builder.graph_summary()["nodes"]
        log.info("check", test="nodes_created", count=count, records=records)
        assert count >= records

    def test_relationships_created(self, built_graph):
        builder = built_graph["builder"]
        expected_sources = built_graph["dataset"]["expected_sources"]
        expected_queries = built_graph["dataset"]["expected_queries"]
        count = builder.graph_summary()["relationships"]
        minimum = expected_sources + expected_queries
        log.info("check", test="relationships_created", count=count, minimum=minimum)
        assert count >= minimum

    def test_record_label_present(self, built_graph):
        labels = built_graph["builder"].graph_summary()["node_labels"]
        log.info("check", test="record_label", labels=labels)
        assert "Record" in labels

    def test_source_label_present(self, built_graph):
        assert "Source" in built_graph["builder"].graph_summary()["node_labels"]

    def test_entity_label_present(self, built_graph):
        assert "Entity" in built_graph["builder"].graph_summary()["node_labels"]

    def test_topic_label_present(self, built_graph):
        assert "Topic" in built_graph["builder"].graph_summary()["node_labels"]

    def test_published_by_present(self, built_graph):
        relationship_types = built_graph["builder"].graph_summary()["relationship_types"]
        assert relationship_types.get("PUBLISHED_BY", 0) >= built_graph["dataset"]["expected_sources"]

    def test_mentions_present(self, built_graph):
        assert built_graph["builder"].graph_summary()["relationship_types"].get("MENTIONS", 0) > 0

    def test_tagged_with_present(self, built_graph):
        relationship_types = built_graph["builder"].graph_summary()["relationship_types"]
        assert relationship_types.get("TAGGED_WITH", 0) >= built_graph["dataset"]["expected_queries"]

    def test_search_returns_results(self, built_graph):
        builder = built_graph["builder"]
        results = builder.search("artificial intelligence", limit=min(3, FETCH_LIMIT))
        log.info("check", test="semantic_search", results_count=len(results))
        assert len(results) > 0


class TestNeo4jGraphFormed:
    def _count(self, session, cypher: str) -> int:
        result = session.run(cypher).single()["c"]
        log.info("neo4j.query", cypher=cypher, result=result)
        return result

    def test_record_nodes_match_fetched_count(self, neo4j_session, built_graph):
        expected = built_graph["dataset"]["expected_records"]
        assert self._count(neo4j_session, "MATCH (n:Record) RETURN count(n) AS c") == expected

    def test_source_nodes_exist(self, neo4j_session):
        assert self._count(neo4j_session, "MATCH (n:Source) RETURN count(n) AS c") > 0

    def test_entity_nodes_exist(self, neo4j_session):
        assert self._count(neo4j_session, "MATCH (n:Entity) RETURN count(n) AS c") > 0

    def test_topic_nodes_exist(self, neo4j_session):
        assert self._count(neo4j_session, "MATCH (n:Topic) RETURN count(n) AS c") > 0

    def test_published_by_relationships_match_sources(self, neo4j_session, built_graph):
        expected = built_graph["dataset"]["expected_sources"]
        assert self._count(neo4j_session, "MATCH ()-[r:PUBLISHED_BY]->() RETURN count(r) AS c") == expected

    def test_mentions_relationships_exist(self, neo4j_session):
        assert self._count(neo4j_session, "MATCH ()-[r:MENTIONS]->() RETURN count(r) AS c") > 0

    def test_tagged_with_relationships_match_queries(self, neo4j_session, built_graph):
        expected = built_graph["dataset"]["expected_queries"]
        assert self._count(neo4j_session, "MATCH ()-[r:TAGGED_WITH]->() RETURN count(r) AS c") == expected

    def test_record_has_title_property(self, neo4j_session, built_graph):
        expected = built_graph["dataset"]["expected_records"]
        assert (
            self._count(
                neo4j_session,
                "MATCH (n:Record) WHERE n.title IS NOT NULL RETURN count(n) AS c",
            )
            == expected
        )

    def test_source_has_name_property(self, neo4j_session):
        assert self._count(
            neo4j_session,
            "MATCH (n:Source) WHERE n.name IS NOT NULL RETURN count(n) AS c",
        ) > 0

    def test_record_connected_to_source(self, neo4j_session, built_graph):
        expected = built_graph["dataset"]["expected_sources"]
        assert (
            self._count(
                neo4j_session,
                "MATCH (r:Record)-[:PUBLISHED_BY]->(s:Source) RETURN count(r) AS c",
            )
            == expected
        )

    def test_total_node_count_scales_with_input(self, neo4j_session, built_graph):
        expected_records = built_graph["dataset"]["expected_records"]
        count = self._count(neo4j_session, "MATCH (n) RETURN count(n) AS c")
        assert count >= expected_records, f"Expected at least {expected_records} nodes, got {count}"

    def test_total_relationship_count_scales_with_input(self, neo4j_session, built_graph):
        expected_minimum = (
            built_graph["dataset"]["expected_sources"] + built_graph["dataset"]["expected_queries"]
        )
        count = self._count(neo4j_session, "MATCH ()-[r]->() RETURN count(r) AS c")
        assert count >= expected_minimum, f"Expected at least {expected_minimum} relationships, got {count}"
