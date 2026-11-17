"""Dynamic Examples loading for Behave features."""

from __future__ import annotations

from typing import Any

from behave_data.config import Config
from behave_data.loaders import load as _load

_LOAD_TAG_PREFIX = "load_examples:"


def _find_load_tag(element: Any, include_parents: bool = True) -> str | None:
    """Find a ``load_examples:<source>`` tag on an element or its ancestors.

    Behave delivers tags without the ``@`` prefix, so both forms are accepted.
    Note that Behave's tag sanitizer strips ``/``, ``\\`` and whitespace from
    tag names — sources containing those characters must be registered in
    ``config.data_sources`` and referenced by name.

    Args:
        element: A Behave object with ``tags`` (scenario, Examples block, etc.).
        include_parents: Also search the element's parents (Rule, Feature).

    Returns:
        The source string (trimmed) if found, else None.
    """
    tags = list(getattr(element, "tags", None) or [])
    if include_parents:
        seen: set[int] = set()
        node = getattr(element, "parent", None)
        # Behave's model is Feature > Rule > Scenario — a few levels at most.
        for _ in range(8):
            if node is None or id(node) in seen:
                break
            seen.add(id(node))
            tags.extend(getattr(node, "tags", None) or [])
            node = getattr(node, "parent", None)
        feature = getattr(element, "feature", None)
        if feature is not None and id(feature) not in seen:
            tags.extend(getattr(feature, "tags", None) or [])

    for tag in tags:
        tag = str(tag).lstrip("@").strip()
        if tag.startswith(_LOAD_TAG_PREFIX):
            return tag[len(_LOAD_TAG_PREFIX) :].strip()
    return None


def _replace_example_rows(example: Any, data: list[dict[str, Any]]) -> None:
    """Replace the rows in an Examples block with loaded data.

    Creates new Row objects preserving line numbers.

    Args:
        example: A Behave Examples object with ``table``.
        data: List of dicts from the loader.
    """
    table = example.table
    if not data:
        table.rows = []
        table.headings = []
        table.modified = True
        return

    # Union of keys in first-seen order so a key that only appears in a later
    # row is not silently dropped.
    headers = list(dict.fromkeys(k for row_data in data for k in row_data))
    base_line = getattr(table, "line", getattr(example, "line", 0))

    def _cell(value: Any) -> str:
        return "" if value is None else str(value)

    try:
        from behave.model import Row
    except ImportError:
        table.headings = headers
        table.rows = [
            _SimpleRow([_cell(row_data.get(h, "")) for h in headers], headers) for row_data in data
        ]
        table.modified = True
        return

    table.headings = headers
    table.rows = [
        Row(headers, [_cell(row_data.get(h, "")) for h in headers], base_line + i + 1)
        for i, row_data in enumerate(data)
    ]
    # Behave only rebuilds outline scenarios whose table is flagged modified;
    # without this, replacing rows after the outline was built has no effect.
    table.modified = True


class _SimpleRow:
    """Fallback Row when behave.model.Row is not available."""

    def __init__(self, cells: list[str], headers: list[str] | None = None) -> None:
        self.cells = cells
        self._headers = headers or []

    def __getitem__(self, index: int) -> str:
        return self.cells[index]

    def as_dict(self) -> dict[str, str]:
        return dict(zip(self._headers, self.cells, strict=False))


def load_examples_for_feature(feature: Any, config: Config) -> None:
    """Load dynamic Examples for all scenarios in a feature.

    Iterates ``feature.scenarios``, finds ``@load_examples:source`` tags,
    and replaces Example rows with data loaded from the source.

    The tag may be placed on the Scenario Outline (applies to all its
    Examples blocks), on a Rule, on the Feature, or on an individual
    Examples block (takes precedence for that block). The tag value is resolved through
    ``config.data_sources`` first, so named sources can hold values that
    Behave's tag sanitizer would mangle (paths with ``/``, URLs, SQL
    queries, etc.).

    Args:
        feature: A Behave Feature object with ``scenarios``.
        config: Configuration for loader resolution.
    """
    # feature.scenarios only covers scenarios outside a Rule — scenarios
    # under a Rule live in rule.scenarios. Iterate both.
    scenarios = list(getattr(feature, "scenarios", []) or [])
    for rule in getattr(feature, "rules", []) or []:
        scenarios.extend(getattr(rule, "scenarios", []) or [])
    if not scenarios:
        return

    cache: dict[str, list[dict[str, Any]]] = {}

    def load_source(source: str) -> list[dict[str, Any]]:
        if source not in cache:
            cache[source] = _load(source, config)
        return cache[source]

    for scenario in scenarios:
        source = _find_load_tag(scenario)
        examples = getattr(scenario, "examples", None) or []
        # An Examples block may carry its own @load_examples tag — it takes
        # precedence over the scenario-level tag for that block, and works
        # even when the scenario itself is untagged.
        block_sources = [_find_load_tag(e, include_parents=False) for e in examples]
        if source is None and all(s is None for s in block_sources):
            continue

        # Load eagerly so an invalid source fails even without Examples.
        data = load_source(source) if source is not None else None

        for example, block_source in zip(examples, block_sources, strict=False):
            effective = block_source if block_source is not None else source
            if effective is None or getattr(example, "table", None) is None:
                continue
            block_data = (
                data if (block_source is None and data is not None) else load_source(effective)
            )
            _replace_example_rows(example, block_data)
