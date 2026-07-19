"""Loader registry and Protocol for behave-data."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from behave_data.config import Config
from behave_data.errors import LoaderNotFoundError
from behave_data.secrets import _validate_path_within_base

_EXTENSION_MAP: dict[str, str] = {
    ".csv": "csv",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xlsx": "xlsx",
}


@runtime_checkable
class Loader(Protocol):
    """Protocol for data loaders."""

    def load(self, source: str, config: Config) -> list[dict[str, Any]]:
        """Load data from a source and return a list of dicts."""
        ...


_LOADERS: dict[str, str] = {
    "csv": "behave_data.loaders.csv:CsvLoader",
    "json": "behave_data.loaders.json:JsonLoader",
    "yaml": "behave_data.loaders.yaml:YamlLoader",
    "xlsx": "behave_data.loaders.excel:ExcelLoader",
    "excel": "behave_data.loaders.excel:ExcelLoader",
    "sql": "behave_data.loaders.sql:SqlLoader",
    "http": "behave_data.loaders.http:HttpLoader",
    "https": "behave_data.loaders.http:HttpLoader",
}

# Matches a URI scheme followed by "://" so that source strings like
# "http://example.com/data" are treated as full URLs, not as "http:" schema prefixes.
_URL_SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")

# Matches an HTTP method prefix followed by a URL, e.g. "GET https://..." or "POST http://...".
_HTTP_METHOD_PATTERN = re.compile(r"^(?:GET|POST)\s+(https?)://", re.IGNORECASE)


def _resolve_loader(schema: str) -> Loader:
    """Lazy-import and return a loader instance for the given schema."""
    if schema not in _LOADERS:
        raise LoaderNotFoundError(schema)
    module_path, class_name = _LOADERS[schema].split(":")
    import importlib

    module = importlib.import_module(module_path)
    loader_cls = getattr(module, class_name)
    loader: Loader = loader_cls()
    return loader


def _detect_schema(source: str) -> str | None:
    """Detect the schema prefix from a source string.

    If source contains a schema prefix (e.g. ``csv:``), return it.
    Otherwise, detect from file extension.

    Also recognizes HTTP method prefixes (``GET URL`` / ``POST URL``)
    as documented by :class:`HttpLoader`.
    """
    method_match = _HTTP_METHOD_PATTERN.match(source.strip())
    if method_match:
        return method_match.group(1)

    if ":" in source:
        prefix = source.split(":", 1)[0].lower()
        if prefix in _LOADERS:
            return prefix
    if _URL_SCHEME_PATTERN.match(source):
        return None
    p = Path(source)
    ext = p.suffix.lower()
    if ext in _EXTENSION_MAP:
        return _EXTENSION_MAP[ext]
    return None


def _resolve_path(source: str, config: Config) -> str:
    """Resolve a source path, using config.load_base_dir for relative paths."""
    p = Path(source)
    if p.is_absolute():
        return source
    if ":" in source:
        raise ValueError(
            f"Relative source path cannot contain ':': {source!r}. "
            "Use an absolute path or remove ':' from the filename."
        )
    base = Path(config.load_base_dir)
    full = base / source
    _validate_path_within_base(full, base)
    return str(full)


def load(source: str, config: Config | None = None) -> list[dict[str, Any]]:
    """Load data from a source string.

    Detects the schema prefix (e.g. ``csv:``) or file extension,
    resolves relative paths against ``config.load_base_dir``,
    and delegates to the appropriate loader.

    Args:
        source: Source string with optional schema prefix.
        config: Configuration with load_base_dir and connection settings.

    Returns:
        List of dicts representing loaded data.

    Raises:
        LoaderNotFoundError: If no loader matches the source.
    """
    cfg = config if config is not None else Config()

    schema = _detect_schema(source)
    if schema is None:
        raise LoaderNotFoundError(source)

    loader = _resolve_loader(schema)

    if (
        ":" in source
        and not _URL_SCHEME_PATTERN.match(source)
        and source.split(":", 1)[0].lower() == schema
    ):
        path = source.split(":", 1)[1]
    else:
        path = source

    if not path.strip():
        raise ValueError(f"Source path cannot be empty after schema prefix: {source!r}")

    if schema not in ("sql", "http", "https"):
        path = _resolve_path(path, cfg)

    return loader.load(path, cfg)
