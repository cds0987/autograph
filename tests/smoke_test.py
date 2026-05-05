"""Smoke tests for the root autograph package."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from autograph import GraphBuilder


def load_test_env() -> dict[str, str | None]:
    """Load environment variables from the repo .env file for local testing."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_model": os.getenv("OPENAI_MODEL"),
        # Support both the current typo in .env and the conventional key names.
        "neo4j_uri": os.getenv("neo4j_url") or os.getenv("neoj4_url"),
        "neo4j_username": os.getenv("neo4j_user") or os.getenv("neoj4_user"),
        "neo4j_password": os.getenv("neo4j_password") or os.getenv("neoj4_password"),
    }


def sample_records() -> list[dict[str, str]]:
    return [
        {
            "id": "1",
            "title": "Acme launches a new AI assistant for hospitals",
            "source": "Acme News",
            "category": "healthcare",
            "summary": "The assistant helps doctors summarize patient notes faster.",
        },
        {
            "id": "2",
            "title": "Blue River studies crop robotics in Vietnam",
            "source": "Field Journal",
            "category": "agriculture",
            "summary": "Researchers test robotics and machine learning for crop monitoring.",
        },
    ]


def run() -> dict[str, object]:
    env = load_test_env()
    builder = GraphBuilder(
        llm_api_key=env["openai_api_key"],
        neo4j_uri=env["neo4j_uri"],
        neo4j_password=env["neo4j_password"],
        use_embeddings=True,
        embedding_provider="local",
        llm_model=env["openai_model"],
        reset_database=True,
    )
    if env["neo4j_username"]:
        builder.config.neo4j_username = env["neo4j_username"]

    builder.load_data(sample_records()).build_graph()
    summary = builder.graph_summary()
    assert summary["records"] == 2
    assert summary["nodes"] >= 2
    assert builder.search("robotics", limit=1)
    assert builder.config.reset_database is True
    return summary


def run_neo4j_integration() -> str:
    """Optional integration test that pushes the sample graph into Neo4j."""
    env = load_test_env()
    if not (env["neo4j_uri"] and env["neo4j_password"]):
        return "Neo4j env vars not configured; skipped."

    builder = GraphBuilder(
        llm_api_key=env["openai_api_key"],
        neo4j_uri=env["neo4j_uri"],
        neo4j_password=env["neo4j_password"],
        use_embeddings=True,
        embedding_provider="local",
        llm_model=env["openai_model"],
        reset_database=True,
    )
    if env["neo4j_username"]:
        builder.config.neo4j_username = env["neo4j_username"]

    builder.load_data(sample_records()).build_graph()
    builder.push_to_neo4j()
    return "Neo4j push completed."


if __name__ == "__main__":
    print(run())
    print(run_neo4j_integration())
