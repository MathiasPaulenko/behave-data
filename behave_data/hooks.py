"""Behave hooks for behave-data."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from behave_data.config import Config
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
    3. First existing file among ``behave_data.yml``, ``behave_data.yaml``,
       ``behave_data.json`` (defaults when none exists)

    Args:
        context: The Behave context object.
        config: Configuration to use. If None, checks userdata then file.
    """
    if config is not None:
        cfg = config
    elif hasattr(context, "config") and hasattr(context.config, "userdata"):
        userdata = context.config.userdata
        if isinstance(userdata, dict) and any(k.startswith("behave_data.") for k in userdata):
            cfg = Config.from_userdata(userdata)
        else:
            cfg = _config_from_file()
    else:
        cfg = _config_from_file()
    context.data = DataManager(cfg)
    apply_patches()


def _config_from_file() -> Config:
    """Load Config from the first config file that exists, or defaults."""
    for candidate in ("behave_data.yml", "behave_data.yaml", "behave_data.json"):
        if Path(candidate).exists():
            return Config.from_file(candidate)
    return Config.from_file("behave_data.yml")


def _resolve_placeholders(value: str, context: Any) -> str:
    """Resolve ``{placeholder}`` patterns in a string using context attributes.

    Supports nested access via dot notation, e.g. ``{user.name}``. Intermediate
    objects may expose attributes (``obj.attr``) or be mappings
    (``mapping[key]``) — mappings are tried by key first.

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
            if part.startswith("_"):
                return match.group(0)
            if isinstance(obj, Mapping):
                if part in obj:
                    obj = obj[part]
                    continue
                return match.group(0)
            if not part.isidentifier():
                return match.group(0)
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return match.group(0)
        return "" if obj is None else str(obj)

    return _PLACEHOLDER_PATTERN.sub(replacer, value)


def before_step_hook(context: Any, step: Any) -> None:
    """Resolve placeholders in table cells and doc strings before each step.

    This hook does NOT mutate the step. If the step has an associated table,
    resolved placeholders are stored in ``context.resolved_table`` as
    ``{"headings": [...], "rows": [...]}``; if it has a doc string, the
    resolved text is stored in ``context.resolved_text``. Both attributes
    are reset to None when the step has no table/text, so stale values from
    a previous step never leak through.

    Placeholders in the step *text* itself cannot be resolved here — Behave
    matches step text to a step definition before this hook runs.

    Args:
        context: The Behave context object.
        step: The step about to be executed.
    """
    table = getattr(step, "table", None)
    if table is None:
        context.resolved_table = None
    else:
        from behave_data.raw_table import RawTable

        raw = RawTable(table)
        resolved_rows: list[list[str]] = []
        for row in raw.rows:
            resolved_rows.append([_resolve_placeholders(cell, context) for cell in row])

        context.resolved_table = {
            "headings": resolved_rows[0],
            "rows": resolved_rows[1:],
        }

    text = getattr(step, "text", None)
    context.resolved_text = _resolve_placeholders(text, context) if isinstance(text, str) else None


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
