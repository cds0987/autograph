"""Tests for validation and sanitization helpers."""

from __future__ import annotations

import pytest

from autograph.utils.validators import ensure_list_of_dicts, sanitize_record
from autograph.core.exceptions import DataValidationError


class TestEnsureListOfDicts:
    def test_list_of_dicts_passthrough(self):
        data = [{"a": 1}, {"a": 2}]
        assert ensure_list_of_dicts(data) == data

    def test_single_dict_wrapped(self):
        result = ensure_list_of_dicts({"a": 1})
        assert result == [{"a": 1}]

    def test_none_raises(self):
        with pytest.raises(DataValidationError):
            ensure_list_of_dicts(None)

    def test_empty_list_raises(self):
        with pytest.raises(DataValidationError):
            ensure_list_of_dicts([])

    def test_list_of_non_dicts_raises(self):
        with pytest.raises(DataValidationError):
            ensure_list_of_dicts([1, 2, 3])

    def test_tuple_of_dicts_accepted(self):
        result = ensure_list_of_dicts(({"a": 1},))
        assert result[0]["a"] == 1


class TestSanitizeRecord:
    def test_removes_none_values(self):
        result = sanitize_record({"a": 1, "b": None})
        assert "b" not in result

    def test_preserves_strings_ints_floats_bools(self):
        record = {"s": "hello", "i": 1, "f": 1.5, "b": True}
        result = sanitize_record(record)
        assert result == record

    def test_stringifies_keys(self):
        result = sanitize_record({1: "val"})
        assert "1" in result

    def test_nested_dict_preserved(self):
        result = sanitize_record({"nested": {"x": 1, "y": 2}})
        assert result["nested"] == {"x": 1, "y": 2}

    def test_list_values_preserved(self):
        result = sanitize_record({"items": [1, "two"]})
        assert result["items"] == [1, "two"]

    def test_datetime_converted_to_isoformat(self):
        import datetime
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        result = sanitize_record({"dt": dt})
        assert result["dt"] == "2024-01-01T12:00:00"
