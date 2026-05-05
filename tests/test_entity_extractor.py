"""Tests for EntityExtractor and helper functions."""

from __future__ import annotations

from autograph.analyzers.entity_extractor import (
    EntityExtractor,
    _dedupe,
    _extract_technology_terms,
    _extract_topics,
    _simple_sentiment,
    _strip_markup,
)
from autograph.core.config import GraphConfig


def _extractor():
    return EntityExtractor(GraphConfig())


def _schema():
    return {
        "title_field": "title",
        "source_field": "source",
        "query_field": "category",
        "text_fields": ["summary"],
    }


class TestEntityExtractor:
    def test_returns_entity_buckets(self, sample_records):
        result = _extractor().extract(sample_records[0], _schema())
        for bucket in ("organizations", "people", "locations", "technologies", "key_topics"):
            assert bucket in result

    def test_sentiment_present(self, sample_records):
        result = _extractor().extract(sample_records[0], _schema())
        assert result["sentiment"] in ("positive", "negative", "neutral")

    def test_existing_entities_passthrough(self):
        record = {
            "title": "Test",
            "entities": {
                "organizations": ["Acme"],
                "people": [],
                "locations": [],
                "technologies": ["AI"],
                "key_topics": [],
                "sentiment": "positive",
            },
        }
        result = _extractor().extract(record, _schema())
        assert "Acme" in result["organizations"]

    def test_technology_detected_in_ai_record(self, sample_records):
        result = _extractor().extract(sample_records[0], _schema())
        techs = [t.lower() for t in result["technologies"]]
        assert any("ai" in t or "machine" in t for t in techs)


class TestHelpers:
    def test_dedupe_preserves_order(self):
        assert _dedupe(["b", "a", "b", "c"]) == ["b", "a", "c"]

    def test_dedupe_case_insensitive(self):
        assert len(_dedupe(["AI", "ai"])) == 1

    def test_strip_markup_removes_html(self):
        assert "<a>" not in _strip_markup("<a>hello</a>")

    def test_simple_sentiment_positive(self):
        assert _simple_sentiment("great advance and improvement") == "positive"

    def test_simple_sentiment_negative(self):
        assert _simple_sentiment("major risk and threat detected") == "negative"

    def test_simple_sentiment_neutral(self):
        assert _simple_sentiment("nothing notable happened") == "neutral"

    def test_extract_technology_terms_finds_ai(self):
        assert "AI" in _extract_technology_terms("AI and machine learning")

    def test_extract_topics_excludes_stopwords(self):
        topics = _extract_topics("the quick brown fox", "", "", {"the", "quick"})
        assert "the" not in topics
        assert "quick" not in topics
