"""Dynamic Examples loading for Behave features."""

from __future__ import annotations

import re
from typing import Any

from behave_data.config import Config
from behave_data.loaders import load as _load

_LOAD_TAG_PATTERN = re.compile(r"@load_examples:(.*)")


def _find_load_tag(scenario: Any) -> str | None:
    """Find a @load_examples:source tag on a scenario or its feature.

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
        match = _LOAD_TAG_PATTERN.match(tag.strip())
        if match:
            return match.group(1).strip()
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

    Args:
        feature: A Behave Feature object with ``scenarios``.
        config: Configuration for loader resolution.
    """
    scenarios = getattr(feature, "scenarios", [])
    if not scenarios:
        return

    for scenario in scenarios:
        source = _find_load_tag(scenario)
        if source is None:
            continue

        data = _load(source, config)

        examples = getattr(scenario, "examples", [])
        if not examples:
            continue

        for example in examples:
            _replace_example_rows(example, data)
