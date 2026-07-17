"""Configuration for behave-data."""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from behave_data.errors import OptionalDependencyError

DEFAULT_NULL_MARKERS: frozenset[str] = frozenset({"", "null", "None", "N/A"})

_KNOWN_KEYS = frozenset(
    {
        "null_markers",
        "null_markers_by_column",
        "secret_backend",
        "secret_path",
        "load_base_dir",
        "db_connections",
        "type_overrides",
    }
)


def _stringify_marker(m: object) -> str:
    """Convert a marker value to string, handling YAML's null -> None."""
    if m is None:
        return "null"
    return str(m)


@dataclass(frozen=True)
class Config:
    """Configuration for behave-data.

    Attributes:
        null_markers: Global set of strings treated as null.
        null_markers_by_column: Per-column null markers that override globals.
        secret_backend: Backend for secret resolution (file, env, vault, aws).
        secret_path: Directory path for file-based secrets.
        load_base_dir: Base directory for relative file loading.
        db_connections: Named database connection strings.
        type_overrides: Per-column type overrides.
    """

    null_markers: frozenset[str] = DEFAULT_NULL_MARKERS
    null_markers_by_column: dict[str, frozenset[str]] = field(default_factory=dict)
    secret_backend: str = "file"
    secret_path: str = "secrets/"
    load_base_dir: str = "features/data/"
    db_connections: dict[str, str] = field(default_factory=dict)
    type_overrides: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create a Config from a dict, filtering unknown keys and converting lists to frozensets.

        Args:
            data: A dict with optional configuration keys.

        Returns:
            A Config instance with values from data, defaults for missing keys.
        """
        filtered = {k: v for k, v in data.items() if k in _KNOWN_KEYS}

        if "null_markers" in filtered:
            val = filtered["null_markers"]
            if isinstance(val, str):
                val = [m.strip() for m in val.split(",")]
            if val is None:
                filtered["null_markers"] = frozenset()
            elif isinstance(val, (list, frozenset, set, tuple)):
                filtered["null_markers"] = frozenset(_stringify_marker(m) for m in val)
            else:
                raise TypeError(f"null_markers must be a list or string, got {type(val).__name__}")

        if "null_markers_by_column" in filtered:
            raw = filtered["null_markers_by_column"]
            converted: dict[str, frozenset[str]] = {}
            for col, markers in raw.items():
                if isinstance(markers, str):
                    markers = [m.strip() for m in markers.split(",")]
                if markers is None:
                    converted[col] = frozenset()
                elif isinstance(markers, (list, frozenset, set, tuple)):
                    converted[col] = frozenset(_stringify_marker(m) for m in markers)
                else:
                    raise TypeError(
                        f"null_markers_by_column[{col!r}] must be a list or string, "
                        f"got {type(markers).__name__}"
                    )
            filtered["null_markers_by_column"] = converted

        return cls(**filtered)

    @classmethod
    def from_file(cls, path: str = "behave_data.yml") -> Config:
        """Load Config from a YAML or JSON file.

        If the file does not exist, returns default Config.
        For ``.yml``/``.yaml`` files, uses PyYAML (lazy-import).
        For ``.json`` files, uses ``json``.
        Unknown extensions return default Config.

        Args:
            path: Path to the configuration file.

        Returns:
            A Config instance.

        Raises:
            OptionalDependencyError: If PyYAML is required but not installed.
        """
        p = Path(path)
        if not p.exists():
            return cls()

        suffix = p.suffix.lower()

        if suffix in (".yml", ".yaml"):
            try:
                import yaml
            except ImportError:
                raise OptionalDependencyError(
                    "pyyaml",
                    "YAML config loading",
                    "pip install behave-data[yaml]",
                ) from None
            with p.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return cls()
            return cls.from_dict(data)

        if suffix == ".json":
            with p.open(encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return cls()
            return cls.from_dict(data)

        return cls()

    @classmethod
    def from_userdata(cls, userdata: dict[str, str]) -> Config:
        """Create a Config from Behave's ``[userdata]`` dict (from ``behave.ini``).

        Keys must be prefixed with ``behave_data.`` to avoid collisions with
        other userdata entries. The prefix is stripped before processing.

        Flat string values are parsed:
        - ``behave_data.null_markers``: comma-separated string
        - ``behave_data.null_markers_by_column``, ``behave_data.db_connections``,
          ``behave_data.type_overrides``: JSON string
        - ``behave_data.secret_backend``, ``behave_data.secret_path``,
          ``behave_data.load_base_dir``: string directly

        Only keys present in *userdata* are used; defaults fill the rest.

        Args:
            userdata: A dict of string key-value pairs, typically from
                ``context.config.userdata``.

        Returns:
            A Config instance with values from userdata, defaults for missing keys.
        """
        prefix = "behave_data."
        filtered = {k[len(prefix) :]: v for k, v in userdata.items() if k.startswith(prefix)}

        data: dict[str, Any] = {}

        if "null_markers" in filtered:
            data["null_markers"] = [m.strip() for m in filtered["null_markers"].split(",")]

        for key in ("secret_backend", "secret_path", "load_base_dir"):
            if key in filtered:
                data[key] = filtered[key]

        for key in ("null_markers_by_column", "db_connections", "type_overrides"):
            if key in filtered:
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    data[key] = json.loads(filtered[key])

        return cls.from_dict(data)
