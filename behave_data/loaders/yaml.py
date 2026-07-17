"""YAML loader for behave-data."""

from __future__ import annotations

from typing import Any

from behave_data.config import Config
from behave_data.errors import OptionalDependencyError


class YamlLoader:
    """Load data from YAML files."""

    def load(self, source: str, config: Config) -> list[dict[str, Any]]:
        """Load YAML data from a file path.

        Args:
            source: Path to the YAML file.
            config: Configuration (unused for YAML, but required by Protocol).

        Returns:
            List of dicts. If the YAML is a dict, wraps it in a list.

        Raises:
            OptionalDependencyError: If PyYAML is not installed.
        """
        try:
            import yaml
        except ImportError:
            raise OptionalDependencyError(
                "pyyaml",
                "YAML loading",
                "pip install behave-data[yaml]",
            ) from None

        with open(source, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError(f"YAML list items must be dicts, got {type(item).__name__}")
            return data
        if isinstance(data, dict):
            return [data]
        if data is None:
            return []
        raise ValueError(f"YAML data must be a list or dict, got {type(data).__name__}")
