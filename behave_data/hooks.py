"""Behave hooks for behave-data."""

from __future__ import annotations

import logging
import re
from typing import Any

from behave_data.config import Config, _KNOWN_KEYS
from behave_data.manager import DataManager
from behave_data.patch import apply_patches

logger = logging.getLogger("behave_data")
logger.addHandler(logging.NullHandler())

_PLACEHOLDER_PATTERN = re.compile(r"\{([^}]+)\}")


def setup_data(context: Any, config: Config | None = None) -> None:
    """Initialize behave-data for a Behave run.

    Stores the configuration, creates a DataManager, and applies table patches.

    Configuration priority:
    1. Explicit ``config`` parameter
    2. ``context.config.userdata`` (from ``behave.ini`` ``[userdata]``)
    3. ``behave_data.yml`` file

    Args:
        context: The Behave context object.
        config: Configuration to use. If None, checks userdata then file.
    """
    if config is not None:
        cfg = config
    elif hasattr(context, "config") and hasattr(context.config, "userdata"):
        userdata = context.config.userdata
        if isinstance(userdata, dict) and any(k in userdata for k in _KNOWN_KEYS):
            cfg = Config.from_userdata(userdata)
        else:
            cfg = Config.from_file("behave_data.yml")
    else:
        cfg = Config.from_file("behave_data.yml")
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


def before_feature_hook(context: Any, feature: Any) -> None:
    """Load dynamic Examples for a feature before it runs.

    If context has no ``data`` attribute, logs a warning and no-ops.

    Args:
        context: The Behave context object.
        feature: The Feature about to run.
    """
    if not hasattr(context, "data"):
        logger.warning("context.data not initialized; skipping examples loading")
        return
    from behave_data.examples import load_examples_for_feature

    config = getattr(context.data, "config", None) or Config()
    load_examples_for_feature(feature, config)


def before_scenario_hook(context: Any, scenario: Any) -> None:
    """Process declarative tags before each scenario.

    If context has no ``data`` attribute, no-ops.

    Args:
        context: The Behave context object.
        scenario: The Scenario about to run.
    """
    if not hasattr(context, "data"):
        return
    from behave_data.tags import process_tags_before_scenario

    process_tags_before_scenario(context, scenario)


def after_scenario_hook(context: Any, scenario: Any) -> None:
    """Execute cleanup after each scenario.

    If context has no ``data`` attribute, no-ops.

    Args:
        context: The Behave context object.
        scenario: The Scenario that just finished.
    """
    if not hasattr(context, "data"):
        return
    from behave_data.tags import process_tags_after_scenario

    process_tags_after_scenario(context, scenario)
