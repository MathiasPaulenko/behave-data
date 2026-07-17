"""CSV loader for behave-data."""

from __future__ import annotations

import csv
from typing import Any

from behave_data.config import Config


class CsvLoader:
    """Load data from CSV files using csv.DictReader."""

    def load(self, source: str, config: Config) -> list[dict[str, Any]]:
        """Load CSV data from a file path.

        Args:
            source: Path to the CSV file.
            config: Configuration (unused for CSV, but required by Protocol).

        Returns:
            List of dicts, one per row. Empty list if file is empty.
        """
        with open(source, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
