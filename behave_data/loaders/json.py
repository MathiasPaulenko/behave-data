"""JSON loader for behave-data."""

from __future__ import annotations

import json
from typing import Any

from behave_data.config import Config


class JsonLoader:
    """Load data from JSON files."""

    def load(self, source: str, config: Config) -> list[dict[str, Any]]:
        """Load JSON data from a file path.

        Args:
            source: Path to the JSON file.
            config: Configuration (unused for JSON, but required by Protocol).

        Returns:
            List of dicts. If the JSON is a dict, wraps it in a list.

        Raises:
            ValueError: If the JSON data is not a list or dict.
        """
        with open(source, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        raise ValueError(f"JSON data must be a list or dict, got {type(data).__name__}")
