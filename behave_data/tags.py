"""Declarative tag processing for data setup and cleanup."""

from __future__ import annotations

from typing import Any


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

    if not hasattr(context, "_behave_data_loaded"):
        context._behave_data_loaded = {}

    for tag in tags:
        if tag.startswith("@needs_data:"):
            name = tag[len("@needs_data:") :]
            data = context.data.fixture(name)
            context._behave_data_loaded[name] = data
        elif tag.startswith("@with_fixture:"):
            name = tag[len("@with_fixture:") :]
            data = context.data.fixture(name)
            setattr(context, name, data)
        elif tag == "@cleanup_after":
            context._behave_data_cleanup = True
            if not hasattr(context, "_behave_data_cleanup_funcs"):
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
    for func in funcs:
        func(context)

    context._behave_data_cleanup = False
