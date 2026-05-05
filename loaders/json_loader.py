"""JSON and JSONL data loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.exceptions import DataValidationError
from ..utils.validators import ensure_list_of_dicts


class JSONLoader:
    """Load records from JSON and JSONL files."""

    def load(self, path: str | Path) -> list[dict[str, Any]]:
        file_path = Path(path)
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            with file_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            return ensure_list_of_dicts(data)
        if suffix == ".jsonl":
            rows: list[dict[str, Any]] = []
            with file_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    rows.append(json.loads(line))
            return ensure_list_of_dicts(rows)
        raise DataValidationError(f"Unsupported JSON file suffix: {suffix}")
