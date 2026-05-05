"""Tests for CSV, JSON, JSONL loaders and AutoDetector."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from autograph.loaders.csv_loader import CSVLoader
from autograph.loaders.json_loader import JSONLoader
from autograph.loaders.auto_detector import AutoDetector
from autograph.core.exceptions import DataValidationError, UnsupportedFormatError


# ---------------------------------------------------------------------------
# CSVLoader
# ---------------------------------------------------------------------------

class TestCSVLoader:
    def test_loads_rows_as_dicts(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")
        rows = CSVLoader().load(f)
        assert len(rows) == 2
        assert rows[0] == {"id": "1", "name": "Alice"}

    def test_returns_list(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("a,b\n1,2\n", encoding="utf-8")
        assert isinstance(CSVLoader().load(f), list)

    def test_handles_utf8_bom(self, tmp_path):
        f = tmp_path / "bom.csv"
        f.write_bytes(b"\xef\xbb\xbfcol\n1\n")
        rows = CSVLoader().load(f)
        assert "col" in rows[0]


# ---------------------------------------------------------------------------
# JSONLoader
# ---------------------------------------------------------------------------

class TestJSONLoader:
    def test_loads_json_array(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps([{"id": "1"}, {"id": "2"}]), encoding="utf-8")
        rows = JSONLoader().load(f)
        assert len(rows) == 2

    def test_loads_single_json_object(self, tmp_path):
        f = tmp_path / "single.json"
        f.write_text(json.dumps({"id": "1", "name": "test"}), encoding="utf-8")
        rows = JSONLoader().load(f)
        assert rows[0]["id"] == "1"

    def test_loads_jsonl(self, tmp_path):
        f = tmp_path / "data.jsonl"
        f.write_text('{"id":"1"}\n{"id":"2"}\n', encoding="utf-8")
        rows = JSONLoader().load(f)
        assert len(rows) == 2

    def test_jsonl_skips_blank_lines(self, tmp_path):
        f = tmp_path / "data.jsonl"
        f.write_text('{"id":"1"}\n\n{"id":"2"}\n', encoding="utf-8")
        rows = JSONLoader().load(f)
        assert len(rows) == 2

    def test_unsupported_suffix_raises(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("{}", encoding="utf-8")
        with pytest.raises(Exception):
            JSONLoader().load(f)


# ---------------------------------------------------------------------------
# AutoDetector
# ---------------------------------------------------------------------------

class TestAutoDetector:
    def test_detects_csv(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("id,name\n1,Alice\n", encoding="utf-8")
        rows = AutoDetector().load(f)
        assert rows[0]["name"] == "Alice"

    def test_detects_json(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps([{"id": "1"}]), encoding="utf-8")
        rows = AutoDetector().load(f)
        assert rows[0]["id"] == "1"

    def test_detects_jsonl(self, tmp_path):
        f = tmp_path / "data.jsonl"
        f.write_text('{"id":"1"}\n', encoding="utf-8")
        rows = AutoDetector().load(f)
        assert rows[0]["id"] == "1"

    def test_accepts_list_of_dicts(self):
        rows = AutoDetector().load([{"a": 1}, {"a": 2}])
        assert len(rows) == 2

    def test_accepts_single_dict(self):
        rows = AutoDetector().load({"a": 1})
        assert rows[0]["a"] == 1

    def test_unsupported_extension_raises(self, tmp_path):
        f = tmp_path / "data.xml"
        f.write_text("<root/>", encoding="utf-8")
        with pytest.raises(UnsupportedFormatError):
            AutoDetector().load(f)
