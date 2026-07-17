"""Behave hooks for behave-data MVP."""

from __future__ import annotations

import re
from typing import Any

from behave_data.config import Config
from behave_data.manager import DataManager
from behave_data.patch import apply_patches

_PLACEHOLDER_PATTERN = re.compile(r"\{([^}]+)\}")


def setup_data(context: Any, config: Config | None = None) -> None:
    """Initialize behave-data for a Behave run.

    Stores the configuration, creates a DataManager, and applies table patches.

    Args:
        context: The Behave context object.
        config: Configuration to use. If None, loads from ``behave_data.yml``.
    """
    cfg = config if config is not None else Config.from_file("behave_data.yml")
    context.data = DataManager(cfg)
    apply_patches()


def _resolve_placeholders(value: str, context: Any) -> str:
    """Resolve ``{placeholder}`` patterns in a string using context attributes.

    Supports nested attribute access via dot notation, e.g. ``{user.name}``.

    Args:
        value: The string potentially containing placeholders.
        context: The Behave context object with attributes.

    Returns:
        The string with placeholders replaced by resolved values.
    """

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        obj: Any = context
        for part in key.split("."):
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return match.group(0)
        return str(obj)

    return _PLACEHOLDER_PATTERN.sub(replacer, value)


def before_step_hook(context: Any, step: Any) -> None:
    """Resolve placeholders in table cells before each step.

    This hook does NOT mutate the original table. If the step has an
    associated table, a copy of the table is created with resolved
    placeholders and assigned to ``context.table``.

    Args:
        context: The Behave context object.
        step: The step about to be executed.
    """
    table = getattr(step, "table", None)
    if table is None:
        return

    from behave_data.raw_table import RawTable

    raw = RawTable(table)
    resolved_rows: list[list[str]] = []
    for row in raw.rows:
        resolved_rows.append([_resolve_placeholders(cell, context) for cell in row])

    context.resolved_table = {
        "headings": list(raw[0]),
        "rows": resolved_rows,
    }
