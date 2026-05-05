"""Validation and normalization helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..core.exceptions import DataValidationError


def ensure_list_of_dicts(records: Any) -> list[dict[str, Any]]:
    """Normalize supported iterables into a list of plain dictionaries."""
    if records is None:
        raise DataValidationError("No records were provided.")

    if _looks_like_dataframe(records):
        return _normalize_dataframe(records)

    if isinstance(records, Mapping):
        return [dict(records)]

    if isinstance(records, Iterable) and not isinstance(records, (str, bytes)):
        normalized: list[dict[str, Any]] = []
        for item in records:
            if isinstance(item, Mapping):
                normalized.append(dict(item))
            else:
                raise DataValidationError(
                    "Each record must be a mapping-like object with key/value pairs."
                )
        if not normalized:
            raise DataValidationError("The provided dataset is empty.")
        return normalized

    raise DataValidationError(
        "Unsupported input data. Use a path, list of dictionaries, mapping, or DataFrame-like object."
    )


def sanitize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Convert nested values into graph-friendly, JSON-serializable shapes."""
    cleaned: dict[str, Any] = {}
    for key, value in record.items():
        if value is None:
            continue
        cleaned[str(key)] = _sanitize_value(value)
    return cleaned


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except TypeError:
            return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _looks_like_dataframe(value: Any) -> bool:
    return hasattr(value, "to_dict") and callable(value.to_dict)


def _normalize_dataframe(frame: Any) -> list[dict[str, Any]]:
    try:
        rows = frame.to_dict(orient="records")
    except TypeError:
        rows = frame.to_dict("records")
    return ensure_list_of_dicts(rows)
