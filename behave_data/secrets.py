"""Secret and placeholder resolution for behave-data."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from behave_data.config import Config
from behave_data.errors import FixtureNotFoundError


def resolve_placeholder(
    value: str,
    config: Config | None = None,
    manager: Any = None,
) -> str | None:
    """Resolve a placeholder string to its actual value.

    Supported prefixes:
        - ``env:VAR_NAME`` — read from environment variable.
        - ``file:relative/path`` — read from file, stripped.
        - ``ref:fixture_name`` — resolve via DataManager.fixture().

    Args:
        value: The placeholder string (e.g. ``env:API_KEY``).
        config: Configuration with secret_path for file backend.
        manager: DataManager instance for ``ref:`` resolution.

    Returns:
        The resolved value, or None if the env var doesn't exist.

    Raises:
        ValueError: If ``ref:`` is used without a manager.
        FixtureNotFoundError: If ``ref:`` fixture is not registered.
        FileNotFoundError: If ``file:`` path doesn't exist.
    """
    cfg = config if config is not None else Config()

    if value.startswith("env:"):
        var_name = value[4:]
        return os.environ.get(var_name)

    if value.startswith("file:"):
        file_path = value[5:]
        full_path = Path(cfg.secret_path) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"Secret file not found: {full_path}")
        return full_path.read_text(encoding="utf-8").strip()

    if value.startswith("ref:"):
        if manager is None:
            raise ValueError("Cannot resolve 'ref:' placeholder without a manager")
        fixture_name = value[4:]
        data = manager.fixture(fixture_name)
        if data is None:
            raise FixtureNotFoundError(fixture_name)
        if isinstance(data, dict):
            return str(data)
        return str(data)

    return value
