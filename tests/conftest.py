"""Shared fixtures for the autograph test suite."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

# Ensure the repo root (parent of autograph/) is on sys.path so
# `import autograph` resolves correctly regardless of how pytest is invoked.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def sample_records():
    return [
        {
            "id": "1",
            "title": "Acme launches a new AI assistant for hospitals",
            "source": "Acme News",
            "category": "healthcare",
            "query": "artificial intelligence",
            "url": "https://example.com/articles/acme-ai-hospitals",
            "summary": "The assistant helps doctors summarize patient notes faster.",
        },
        {
            "id": "2",
            "title": "Blue River studies crop robotics in Vietnam",
            "source": "Field Journal",
            "category": "agriculture",
            "query": "robotics",
            "url": "https://example.com/articles/blue-river-robotics",
            "summary": "Researchers test robotics and machine learning for crop monitoring.",
        },
    ]


@pytest.fixture(scope="session")
def sample_data_dir(tmp_path_factory, sample_records):
    data_dir = tmp_path_factory.mktemp("sample_data")

    json_file = data_dir / "ai_articles.json"
    json_file.write_text(json.dumps(sample_records, indent=2), encoding="utf-8")

    jsonl_file = data_dir / "ai_articles.jsonl"
    with jsonl_file.open("w", encoding="utf-8", newline="") as handle:
        for record in sample_records:
            handle.write(json.dumps(record) + "\n")

    csv_file = data_dir / "ai_articles.csv"
    with csv_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "title", "source", "category", "query", "url", "summary"],
        )
        writer.writeheader()
        writer.writerows(sample_records)

    return data_dir


@pytest.fixture()
def csv_path(sample_data_dir):
    return sample_data_dir / "ai_articles.csv"


@pytest.fixture()
def json_path(sample_data_dir):
    return sample_data_dir / "ai_articles.json"


@pytest.fixture()
def jsonl_path(sample_data_dir):
    return sample_data_dir / "ai_articles.jsonl"
