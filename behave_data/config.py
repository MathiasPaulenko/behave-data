"""Configuration for behave-data."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from behave_data.errors import BehaveDataError, OptionalDependencyError

logger = logging.getLogger("behave_data")
logger.addHandler(logging.NullHandler())

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

    def __post_init__(self) -> None:
        """Validate field types."""
        if not isinstance(self.null_markers, frozenset):
            raise TypeError(
                f"null_markers must be a frozenset, got {type(self.null_markers).__name__}"
            )
        for marker in self.null_markers:
            if not isinstance(marker, str):
                raise TypeError(
                    f"null_markers must contain only strings, got {type(marker).__name__}"
                )

        if not isinstance(self.null_markers_by_column, dict):
            raise TypeError(
                "null_markers_by_column must be a dict, "
                f"got {type(self.null_markers_by_column).__name__}"
            )
        for key, markers in self.null_markers_by_column.items():
            if not isinstance(markers, frozenset):
                raise TypeError(
                    f"null_markers_by_column[{key!r}] must be a frozenset, "
                    f"got {type(markers).__name__}"
                )
            for marker in markers:
                if not isinstance(marker, str):
                    raise TypeError(
                        f"null_markers_by_column[{key!r}] must contain only strings, "
                        f"got {type(marker).__name__}"
                    )

        if not isinstance(self.secret_backend, str):
            raise TypeError(
                f"secret_backend must be a str, got {type(self.secret_backend).__name__}"
            )
        if not isinstance(self.secret_path, str):
            raise TypeError(f"secret_path must be a str, got {type(self.secret_path).__name__}")
        if not isinstance(self.load_base_dir, str):
            raise TypeError(f"load_base_dir must be a str, got {type(self.load_base_dir).__name__}")

        if not isinstance(self.type_overrides, dict):
            raise TypeError(
                f"type_overrides must be a dict, got {type(self.type_overrides).__name__}"
            )
        for key, override in self.type_overrides.items():
            if not isinstance(override, str):
                raise TypeError(
                    f"type_overrides[{key!r}] must be a string, got {type(override).__name__}"
                )

        if not isinstance(self.db_connections, dict):
            raise TypeError(
                f"db_connections must be a dict, got {type(self.db_connections).__name__}"
            )
        for key, connection in self.db_connections.items():
            if not isinstance(connection, str):
                raise TypeError(
                    f"db_connections[{key!r}] must be a string, got {type(connection).__name__}"
                )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create a Config from a dict, filtering unknown keys and converting lists to frozensets.

        Args:
            data: A dict with optional configuration keys.

        Returns:
            A Config instance with values from data, defaults for missing keys.
        """
        filtered = {k: v for k, v in data.items() if k in _KNOWN_KEYS}

        # Treat explicit nulls for mapping/string fields as "use the default"
        # (except for null_markers, where None means an empty frozenset).
        for key in list(filtered):
            if filtered[key] is None and key != "null_markers":
                del filtered[key]

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
            if not isinstance(raw, dict):
                raise TypeError(f"null_markers_by_column must be a dict, got {type(raw).__name__}")
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
        Unknown extensions raise ``ValueError``.

        Args:
            path: Path to the configuration file.

        Returns:
            A Config instance.

        Raises:
            ValueError: If the file extension is not .yml/.yaml/.json.
            BehaveDataError: If the file content is malformed or not a mapping.
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
            try:
                with p.open(encoding="utf-8-sig") as f:
                    data = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                raise BehaveDataError(f"Malformed YAML in config file '{path}': {exc}") from exc
            if not isinstance(data, dict):
                raise BehaveDataError(
                    f"Config file '{path}' must contain a mapping at the top level, "
                    f"got {type(data).__name__}"
                )
            return cls.from_dict(data)

        if suffix == ".json":
            try:
                with p.open(encoding="utf-8-sig") as f:
                    data = json.load(f)
            except json.JSONDecodeError as exc:
                raise BehaveDataError(f"Malformed JSON in config file '{path}': {exc}") from exc
            if not isinstance(data, dict):
                raise BehaveDataError(
                    f"Config file '{path}' must contain a mapping at the top level, "
                    f"got {type(data).__name__}"
                )
            return cls.from_dict(data)

        raise ValueError(
            f"Unsupported config file extension '{suffix}'. Use .yml, .yaml, or .json."
        )

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
            val = filtered["null_markers"]
            if not isinstance(val, str):
                val = str(val)
            data["null_markers"] = [m.strip() for m in val.split(",")]

        for key in ("secret_backend", "secret_path", "load_base_dir"):
            if key in filtered:
                val = filtered[key]
                if not isinstance(val, str):
                    val = str(val)
                data[key] = val

        for key in ("null_markers_by_column", "db_connections", "type_overrides"):
            if key in filtered:
                try:
                    data[key] = json.loads(filtered[key])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(
                        "Invalid JSON for behave_data.%s in userdata — ignoring. Value: %r",
                        key,
                        filtered[key],
                    )

        return cls.from_dict(data)
