"""Declarative tag processing for data setup and cleanup."""

from __future__ import annotations

import inspect
import logging
from typing import Any

from behave_data.errors import BehaveDataError

logger = logging.getLogger(__name__)

# Attributes that must never be overwritten by tag-driven fixture assignment.
_RESERVED_CONTEXT_ATTRS = frozenset({"data", "config", "feature", "scenario"})

# Behave's model is Feature > Rule > Scenario — a few levels at most. The bound
# also protects against pathological objects (e.g. mocks whose .parent keeps
# returning new objects) producing an endless chain.
_MAX_PARENT_DEPTH = 8


def _safe_attr_name(name: str) -> str | None:
    """Return a context attribute name for a fixture name, or None.

    Parametrized fixtures (``name:param``) map to ``name_param`` so each
    parameter gets its own context attribute. Names that aren't valid
    identifiers, start with an underscore, or would clobber reserved
    context attributes are rejected.

    Args:
        name: The fixture name from the tag.

    Returns:
        A safe attribute name, or None if none can be derived.
    """
    attr = name.replace(":", "_")
    if not attr.isidentifier() or attr.startswith("_") or attr in _RESERVED_CONTEXT_ATTRS:
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

    # Collect tags from the scenario, its parents (Rule, Feature), and the
    # feature itself — Behave scenarios under a Rule inherit the rule's tags.
    tags = list(getattr(scenario, "tags", None) or [])
    seen: set[int] = set()
    node = getattr(scenario, "parent", None)
    for _ in range(_MAX_PARENT_DEPTH):
        if node is None or id(node) in seen:
            break
        seen.add(id(node))
        tags.extend(getattr(node, "tags", None) or [])
        node = getattr(node, "parent", None)
    feature = getattr(scenario, "feature", None)
    if feature is not None and id(feature) not in seen:
        tags.extend(getattr(feature, "tags", None) or [])

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

    funcs = getattr(context, "_behave_data_cleanup_funcs", None) or []
    if callable(funcs):
        funcs = [funcs]
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
