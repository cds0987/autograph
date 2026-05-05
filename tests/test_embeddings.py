"""Tests for EmbeddingGenerator, LocalTfidfEmbeddingProvider, and VectorIndex."""

from __future__ import annotations

import pytest

from autograph.embeddings.embedding_generator import (
    EmbeddingGenerator,
    LocalTfidfEmbeddingProvider,
)
from autograph.embeddings.vector_index import VectorIndex
from autograph.core.config import GraphConfig
from autograph.core.exceptions import ConfigurationError


class TestLocalTfidfEmbeddingProvider:
    def test_embed_returns_list_of_floats(self):
        provider = LocalTfidfEmbeddingProvider(dimensions=16)
        provider.prepare(["hello world", "foo bar"])
        vector = provider.embed_text("hello world")
        assert isinstance(vector, list)
        assert all(isinstance(v, float) for v in vector)

    def test_vector_length_equals_dimensions(self):
        # vocabulary is capped at dimensions; vector length == vocab size (<= dimensions)
        provider = LocalTfidfEmbeddingProvider(dimensions=32)
        provider.prepare(["some text here"])
        vector = provider.embed_text("some text here")
        assert len(vector) <= 32

    def test_prepare_builds_vocabulary(self):
        provider = LocalTfidfEmbeddingProvider(dimensions=16)
        provider.prepare(["machine learning rocks"])
        assert len(provider.vocabulary) > 0

    def test_embed_without_prepare_still_works(self):
        provider = LocalTfidfEmbeddingProvider(dimensions=16)
        vector = provider.embed_text("standalone text")
        assert len(vector) > 0

    def test_cosine_similarity_identical_vectors_is_one(self):
        provider = LocalTfidfEmbeddingProvider(dimensions=16)
        provider.prepare(["robotics and AI"])
        v = provider.embed_text("robotics and AI")
        sim = EmbeddingGenerator.cosine_similarity(v, v)
        assert abs(sim - 1.0) < 1e-6


class TestEmbeddingGenerator:
    def test_local_provider_selected_by_default(self):
        gen = EmbeddingGenerator(GraphConfig(embedding_provider="local"))
        assert isinstance(gen.provider, LocalTfidfEmbeddingProvider)

    def test_unsupported_provider_raises(self):
        with pytest.raises(ConfigurationError):
            EmbeddingGenerator(GraphConfig(embedding_provider="unknown"))

    def test_prepare_and_embed(self):
        gen = EmbeddingGenerator(GraphConfig(embedding_provider="local"))
        gen.prepare(["text one", "text two"])
        vector = gen.embed_text("text one")
        assert len(vector) > 0


class TestVectorIndex:
    def _make_index(self):
        gen = EmbeddingGenerator(GraphConfig(embedding_provider="local"))
        gen.prepare(["AI in healthcare", "crop robotics in Vietnam"])
        return VectorIndex(gen)

    def test_add_and_search_returns_results(self):
        index = self._make_index()
        index.add("doc1", "AI in healthcare", {"title": "AI article"})
        index.add("doc2", "crop robotics in Vietnam", {"title": "Robotics article"})
        results = index.search("healthcare AI", limit=1)
        assert len(results) == 1

    def test_search_result_has_score(self):
        index = self._make_index()
        index.add("doc1", "AI in healthcare", {"title": "AI"})
        results = index.search("AI")
        assert "score" in results[0]

    def test_limit_respected(self):
        index = self._make_index()
        index.add("doc1", "AI in healthcare", {})
        index.add("doc2", "crop robotics", {})
        results = index.search("technology", limit=1)
        assert len(results) == 1

    def test_most_relevant_ranked_first(self):
        index = self._make_index()
        index.add("doc1", "AI in healthcare systems", {})
        index.add("doc2", "crop robotics in Vietnam", {})
        results = index.search("healthcare AI")
        assert results[0]["id"] == "doc1"
