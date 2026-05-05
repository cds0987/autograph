"""Provider-based embedding generation."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Protocol

from ..core.config import GraphConfig
from ..core.exceptions import ConfigurationError, IntegrationUnavailableError


class EmbeddingProvider(Protocol):
    """Common interface for interchangeable embedding backends."""

    def prepare(self, texts: list[str]) -> None:
        """Optional corpus preparation step."""

    def embed_text(self, text: str) -> list[float]:
        """Return an embedding vector for one text."""


class LocalTfidfEmbeddingProvider:
    """Offline local embeddings using a lightweight TF-IDF style vocabulary."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions
        self.vocabulary: dict[str, int] = {}
        self.idf: dict[str, float] = {}

    def prepare(self, texts: list[str]) -> None:
        document_frequency: Counter[str] = Counter()
        token_counts: Counter[str] = Counter()
        tokenized_docs: list[list[str]] = []

        for text in texts:
            tokens = self._tokens(text)
            tokenized_docs.append(tokens)
            unique_tokens = set(tokens)
            document_frequency.update(unique_tokens)
            token_counts.update(tokens)

        ranked_terms = [
            term
            for term, _ in sorted(token_counts.items(), key=lambda item: (-item[1], item[0]))
            if len(term) > 1
        ][: self.dimensions]
        self.vocabulary = {term: index for index, term in enumerate(ranked_terms)}

        document_count = max(len(tokenized_docs), 1)
        self.idf = {
            term: math.log((1 + document_count) / (1 + document_frequency[term])) + 1.0
            for term in self.vocabulary
        }

    def embed_text(self, text: str) -> list[float]:
        if not self.vocabulary:
            self.prepare([text])

        tokens = self._tokens(text)
        vector = [0.0] * len(self.vocabulary)
        if not tokens:
            return vector

        term_frequency = Counter(tokens)
        token_total = len(tokens)
        for term, count in term_frequency.items():
            index = self.vocabulary.get(term)
            if index is None:
                continue
            tf = count / token_total
            vector[index] = tf * self.idf.get(term, 1.0)

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9][a-zA-Z0-9._-]{1,}", text.lower())


class OpenAIEmbeddingProvider:
    """API-backed embeddings via OpenAI."""

    def __init__(self, config: GraphConfig) -> None:
        if not config.llm_api_key:
            raise ConfigurationError(
                "An API key is required for OpenAI embeddings."
            )
        self.api_key = config.llm_api_key
        self.model = config.embedding_model or "text-embedding-3-small"

    def prepare(self, texts: list[str]) -> None:
        return None

    def embed_text(self, text: str) -> list[float]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise IntegrationUnavailableError("The openai package is not installed.") from exc

        client = OpenAI(api_key=self.api_key)
        response = client.embeddings.create(model=self.model, input=text)
        return list(response.data[0].embedding)


class EmbeddingGenerator:
    """Facade that selects an embedding provider based on configuration."""

    def __init__(self, config: GraphConfig) -> None:
        self.config = config
        self.provider = self._build_provider()

    def prepare(self, texts: list[str]) -> None:
        self.provider.prepare(texts)

    def embed_text(self, text: str) -> list[float]:
        return self.provider.embed_text(text)

    @staticmethod
    def cosine_similarity(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right))

    def _build_provider(self) -> EmbeddingProvider:
        provider = self.config.embedding_provider.lower()
        if provider == "local":
            return LocalTfidfEmbeddingProvider(dimensions=self.config.local_embedding_dimensions)
        if provider == "openai":
            return OpenAIEmbeddingProvider(self.config)
        raise ConfigurationError(f"Unsupported embedding_provider: {self.config.embedding_provider}")
