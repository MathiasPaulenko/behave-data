"""Declarative tag processing for data setup and cleanup."""

from __future__ import annotations

import inspect
import logging
from typing import Any

from behave_data.errors import BehaveDataError

logger = logging.getLogger("behave_data")
logger.addHandler(logging.NullHandler())

# Attributes that must never be overwritten by tag-driven fixture assignment.
_RESERVED_CONTEXT_ATTRS = frozenset({"data", "config", "feature", "scenario"})


def _safe_attr_name(name: str) -> str | None:
    """Return a context attribute name for a fixture name, or None.

    Parametrized fixtures (``name:param``) map to the base name — the
    full ``name:param`` string can't be accessed via dot notation anyway.
    Names that aren't valid identifiers or that would clobber reserved
    context attributes are rejected.

    Args:
        name: The fixture name from the tag.

    Returns:
        A safe attribute name, or None if none can be derived.
    """
    attr = name if name.isidentifier() else name.partition(":")[0]
    if not attr.isidentifier() or attr in _RESERVED_CONTEXT_ATTRS:
        return None
    return attr


def process_tags_before_scenario(context: Any, scenario: Any) -> None:
    """Process declarative tags before a scenario runs.

    Supported tags:
        - @needs_data:name — calls context.data.fixture(name)
        - @with_fixture:name — calls context.data.fixture(name), assigns to context
        - @cleanup_after — sets cleanup flag

    Args:
        context: The Behave context object.
        scenario: The Scenario about to run.
    """
    if not hasattr(context, "data"):
        return

    tags = list(getattr(scenario, "tags", []))
    feature = getattr(scenario, "feature", None)
    if feature is not None:
        tags.extend(getattr(feature, "tags", []))

    if getattr(context, "_behave_data_loaded", None) is None:
        context._behave_data_loaded = {}

    # Defensive reset: a leftover cleanup flag means the previous after_scenario
    # hook did not run, so stale cleanup functions must not leak into this one.
    if getattr(context, "_behave_data_cleanup", False):
        context._behave_data_cleanup = False
        context._behave_data_cleanup_funcs = []

    for tag in tags:
        tag = tag.lstrip("@")
        if tag.startswith("needs_data:"):
            name = tag[len("needs_data:") :].strip()
            if not name:
                raise ValueError("needs_data tag requires a fixture name")
            data = context.data.fixture(name)
            context._behave_data_loaded[name] = data
            attr = _safe_attr_name(name)
            if attr is not None:
                setattr(context, attr, data)
            else:
                logger.warning(
                    "Fixture %r is not a usable attribute name; "
                    "access it via context._behave_data_loaded[%r]",
                    name,
                    name,
                )
        elif tag.startswith("with_fixture:"):
            name = tag[len("with_fixture:") :].strip()
            if not name:
                raise ValueError("with_fixture tag requires a fixture name")
            data = context.data.fixture(name)
            attr = _safe_attr_name(name)
            if attr is not None:
                setattr(context, attr, data)
            else:
                logger.warning(
                    "Fixture %r is not a usable attribute name; access it via getattr(context, %r)",
                    name,
                    name,
                )
        elif tag == "cleanup_after":
            context._behave_data_cleanup = True
            context._behave_data_cleanup_funcs = []


def process_tags_after_scenario(context: Any, scenario: Any) -> None:
    """Execute cleanup functions after a scenario runs.

    If ``context._behave_data_cleanup`` is True, executes callables in
    ``context._behave_data_cleanup_funcs``. Clears the flag afterward.

    Args:
        context: The Behave context object.
        scenario: The Scenario that just finished.
    """
    if not getattr(context, "_behave_data_cleanup", False):
        return

    funcs = getattr(context, "_behave_data_cleanup_funcs", [])
    first_error: Exception | None = None
    try:
        for func in funcs:
            try:
                if not callable(func):
                    raise BehaveDataError(
                        f"Cleanup function must be callable, got {type(func).__name__}"
                    )
                try:
                    sig = inspect.signature(func)
                except (ValueError, TypeError):
                    func()
                else:
                    if len(sig.parameters) > 0:
                        func(context)
                    else:
                        func()
            except Exception as exc:
                if first_error is None:
                    first_error = exc
    finally:
        context._behave_data_cleanup = False
        context._behave_data_cleanup_funcs = []
    if first_error is not None:
        raise first_error
