"""Configuration models for the graph builder."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GraphConfig:
    """User-facing configuration for graph construction."""

    llm_api_key: str | None = None
    llm_provider: str = "openai"
    llm_model: str | None = None
    embedding_provider: str = "local"
    embedding_model: str | None = None
    neo4j_uri: str | None = None
    neo4j_username: str = "neo4j"
    neo4j_password: str | None = None
    reset_database: bool = True
    use_embeddings: bool = False
    use_llm: bool = False
    batch_size: int = 100
    sample_size: int = 25
    verbose: bool = False
    article_label: str = "Record"
    source_label: str = "Source"
    entity_label: str = "Entity"
    query_label: str = "Topic"
    local_embedding_dimensions: int = 256
    stopwords: set[str] = field(
        default_factory=lambda: {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "in",
            "into",
            "is",
            "it",
            "of",
            "on",
            "or",
            "that",
            "the",
            "their",
            "this",
            "to",
            "with",
        }
    )
