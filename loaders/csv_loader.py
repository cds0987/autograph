"""Delimited text file loaders."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class CSVLoader:
    """Load records from CSV files."""

    def load(self, path: str | Path) -> list[dict[str, Any]]:
        file_path = Path(path)
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]
