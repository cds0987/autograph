"""Entity extraction with heuristics-first behavior."""

from __future__ import annotations

import html
import re
from typing import Any

from ..core.config import GraphConfig
from ..utils.llm_client import LLMClient

ENTITY_BUCKETS = ("organizations", "people", "locations", "technologies", "key_topics")
TECH_TERMS = {
    "ai",
    "a.i.",
    "artificial intelligence",
    "machine learning",
    "llm",
    "llms",
    "robot",
    "robotics",
    "cybersecurity",
    "cyberwar",
    "software",
    "model",
    "models",
}
LOCATION_HINTS = {"city", "state", "county", "house", "university", "paris", "london", "tokyo"}


class EntityExtractor:
    """Extract structured entities from generic records."""

    def __init__(self, config: GraphConfig) -> None:
        self.config = config
        self.llm_client = LLMClient(config)

    def extract(self, record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        existing = record.get("entities")
        if isinstance(existing, dict):
            return self._normalize_entities(existing)

        heuristic = self._heuristic_extract(record, schema)
        if not self.llm_client.is_enabled():
            return heuristic

        # LLM output is optional. If parsing fails, heuristics still win.
        prompt = self._build_prompt(record, schema)
        response = self.llm_client.complete_json(prompt)
        text = response.get("raw_text", "")
        llm_entities = self._parse_jsonish_response(text)
        if llm_entities:
            return self._merge_entities(heuristic, self._normalize_entities(llm_entities))
        return heuristic

    def _heuristic_extract(self, record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        text_parts: list[str] = []
        for field in schema.get("text_fields", []):
            value = record.get(field)
            if value:
                text_parts.append(str(value))
        text = " ".join(text_parts) or " ".join(str(value) for value in record.values() if isinstance(value, str))
        plain_text = _strip_markup(text)
        title = str(record.get(schema.get("title_field") or "", "")).strip()
        source = str(record.get(schema.get("source_field") or "", "")).strip()
        query = str(record.get(schema.get("query_field") or "", "")).strip()

        organizations = _dedupe([source] if source else [])
        organizations.extend(_extract_title_case_phrases(title))
        organizations = _dedupe([item for item in organizations if len(item) > 2])

        people = _extract_people_names(plain_text)
        technologies = _extract_technology_terms(" ".join([title, plain_text]))
        locations = _extract_locations(" ".join([title, plain_text]))
        key_topics = _extract_topics(title, query, plain_text, self.config.stopwords)

        return {
            "organizations": organizations,
            "people": people,
            "locations": locations,
            "technologies": technologies,
            "key_topics": key_topics,
            "sentiment": _simple_sentiment(" ".join([title, plain_text])),
        }

    def _build_prompt(self, record: dict[str, Any], schema: dict[str, Any]) -> str:
        return (
            "Extract structured entities from this record and return JSON with keys "
            f"{', '.join(ENTITY_BUCKETS)}, sentiment.\n"
            f"Schema hints: {schema}\nRecord: {record}"
        )

    @staticmethod
    def _parse_jsonish_response(text: str) -> dict[str, Any] | None:
        if not text:
            return None
        import json

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _normalize_entities(entities: dict[str, Any]) -> dict[str, Any]:
        normalized = {bucket: [] for bucket in ENTITY_BUCKETS}
        for bucket in ENTITY_BUCKETS:
            value = entities.get(bucket, [])
            if isinstance(value, str):
                value = [value]
            if isinstance(value, list):
                normalized[bucket] = _dedupe([str(item).strip() for item in value if str(item).strip()])
        normalized["sentiment"] = str(entities.get("sentiment", "neutral")).lower()
        return normalized

    @staticmethod
    def _merge_entities(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
        merged = {}
        for bucket in ENTITY_BUCKETS:
            merged[bucket] = _dedupe(base.get(bucket, []) + incoming.get(bucket, []))
        merged["sentiment"] = incoming.get("sentiment") or base.get("sentiment", "neutral")
        return merged


def _strip_markup(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(without_tags).replace("\xa0", " ")


def _extract_title_case_phrases(text: str) -> list[str]:
    pattern = re.compile(r"\b(?:[A-Z][\w&.-]+(?:\s+[A-Z][\w&.-]+){0,4})\b")
    return [match.group(0).strip() for match in pattern.finditer(text)]


def _extract_people_names(text: str) -> list[str]:
    candidates = []
    for phrase in _extract_title_case_phrases(text):
        parts = phrase.split()
        if 1 < len(parts) <= 3 and all(part[0].isupper() for part in parts if part):
            candidates.append(phrase)
    return _dedupe(candidates[:10])


def _extract_technology_terms(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for term in sorted(TECH_TERMS):
        if term in lowered:
            found.append(term.upper() if term == "ai" else term.title())
    return _dedupe(found)


def _extract_locations(text: str) -> list[str]:
    locations = []
    for phrase in _extract_title_case_phrases(text):
        lowered = phrase.lower()
        if any(hint in lowered for hint in LOCATION_HINTS):
            locations.append(phrase)
    return _dedupe(locations[:10])


def _extract_topics(title: str, query: str, text: str, stopwords: set[str]) -> list[str]:
    candidate_text = " ".join([title, query, text]).lower()
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9.-]{2,}", candidate_text)
    counts: dict[str, int] = {}
    for word in words:
        if word in stopwords:
            continue
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ranked[:8]]


def _simple_sentiment(text: str) -> str:
    lowered = text.lower()
    positive = sum(term in lowered for term in ("win", "growth", "benefit", "advance", "improve"))
    negative = sum(term in lowered for term in ("risk", "threat", "loss", "hack", "undermine"))
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        key = item.strip()
        normalized = key.casefold()
        if not key or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(key)
    return ordered
