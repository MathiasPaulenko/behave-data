"""Dynamic Examples loading for Behave features."""

from __future__ import annotations

from typing import Any

from behave_data.config import Config
from behave_data.loaders import load as _load

_LOAD_TAG_PREFIX = "load_examples:"


def _find_load_tag(scenario: Any) -> str | None:
    """Find a ``load_examples:<source>`` tag on a scenario or its feature.

    Behave delivers tags without the ``@`` prefix, so both forms are accepted.
    Note that Behave's tag sanitizer strips ``/``, ``\\`` and whitespace from
    tag names — sources containing those characters must be registered in
    ``config.data_sources`` and referenced by name.

    Args:
        scenario: A Behave scenario object with ``tags`` and ``feature.tags``.

    Returns:
        The source string (trimmed) if found, else None.
    """
    tags = list(getattr(scenario, "tags", []))
    feature = getattr(scenario, "feature", None)
    if feature is not None:
        tags.extend(getattr(feature, "tags", []))

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
    if not data:
        example.table.rows = []
        example.table.headings = []
        return

    headers = list(data[0].keys())

    def _cell(value: Any) -> str:
        return "" if value is None else str(value)

    try:
        from behave.model import Row
    except ImportError:
        example.table.headings = headers
        example.table.rows = []
        for row_data in data:
            cells = [_cell(row_data.get(h, "")) for h in headers]
            example.table.rows.append(_SimpleRow(cells, headers))
        return

    example.table.headings = headers
    example.table.rows = []
    for row_data in data:
        cells = [_cell(row_data.get(h, "")) for h in headers]
        line = getattr(example, "line", 0)
        example.table.rows.append(Row(headers, cells, line))


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
    Examples blocks), on the Feature, or on an individual Examples block
    (takes precedence for that block). The tag value is resolved through
    ``config.data_sources`` first, so named sources can hold values that
    Behave's tag sanitizer would mangle (paths with ``/``, URLs, SQL
    queries, etc.).

    Args:
        feature: A Behave Feature object with ``scenarios``.
        config: Configuration for loader resolution.
    """
    scenarios = getattr(feature, "scenarios", [])
    if not scenarios:
        return

    cache: dict[str, list[dict[str, Any]]] = {}

    def load_source(source: str) -> list[dict[str, Any]]:
        if source not in cache:
            cache[source] = _load(source, config)
        return cache[source]

    for scenario in scenarios:
        source = _find_load_tag(scenario)
        if source is None:
            continue

        # Load eagerly so an invalid source fails even without Examples.
        data = load_source(source)

        examples = getattr(scenario, "examples", [])
        if not examples:
            continue

        for example in examples:
            # An Examples block may carry its own @load_examples tag.
            block_source = _find_load_tag(example)
            block_data = load_source(block_source) if block_source is not None else data
            table = getattr(example, "table", None)
            if table is None:
                continue
            _replace_example_rows(example, block_data)
