"""Shared fixtures for the autograph test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the repo root (parent of autograph/) is on sys.path so
# `import autograph` resolves correctly regardless of how pytest is invoked.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture()
def sample_records():
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


@pytest.fixture()
def csv_path():
    return DATA_DIR / "ai_articles.csv"


@pytest.fixture()
def json_path():
    return DATA_DIR / "ai_articles.json"


@pytest.fixture()
def jsonl_path():
    return DATA_DIR / "ai_articles.jsonl"
