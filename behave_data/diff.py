"""Table diff with Cucumber-style output."""

from __future__ import annotations

from collections import Counter
from typing import Any

from behave_tables.wrapper import TableWrapper

from behave_data.errors import TableDiffError


def diff(
    expected: Any,
    actual: Any,
    *,
    ordered: bool = True,
    ignore_columns: list[str] | None = None,
    surplus_columns: bool = True,
) -> None:
    """Compare two tables and raise TableDiffError if they differ.

    Args:
        expected: The expected data. Accepts a table-like object (with
            ``headings`` and ``rows``), ``list[dict]``, or a single ``dict``.
        actual: The actual data. Accepts a table-like object, ``list[dict]``,
            or a single ``dict`` (wrapped in a list). ``list[list]`` raises
            ``ValueError`` because headers are needed.
        ordered: If True, rows must be in the same order.
        ignore_columns: Column names to exclude from comparison.
        surplus_columns: If False, extra columns in actual are removed before
            comparison (they don't cause a diff).

    Raises:
        ValueError: If either side is a ``list[list]`` (needs headers).
        TypeError: If a side is not a table-like object, list, or dict.
        TableDiffError: If the tables differ, with a Cucumber-style diff output.
    """
    ignore_set = set(ignore_columns) if ignore_columns else set()

    exp_headers, exp_rows = _normalize_table(expected, "expected")
    exp_headers = [h for h in exp_headers if h not in ignore_set]

    act_headers, act_rows = _normalize_table(actual, "actual")

    # An empty actual list has no headers of its own — compare against
    # the expected headers so it diffs purely on missing rows.
    if isinstance(actual, list) and not actual:
        act_headers = list(exp_headers)

    # Filter ignore_columns from actual
    act_headers = [h for h in act_headers if h not in ignore_set]
    act_rows = [{k: v for k, v in row.items() if k not in ignore_set} for row in act_rows]

    # Filter ignore_columns from expected
    exp_rows = [{k: v for k, v in row.items() if k not in ignore_set} for row in exp_rows]

    # Handle surplus columns
    if not surplus_columns:
        exp_set = set(exp_headers)
        act_rows = [{k: v for k, v in row.items() if k in exp_set} for row in act_rows]
        act_headers = [h for h in act_headers if h in exp_set]

    # Build diff output
    diff_lines: list[str] = []

    # Header diff
    if exp_headers != act_headers:
        diff_lines.append("Tables were not identical:")
        diff_lines.append(f"  Headers differ: expected {exp_headers}, got {act_headers}")
        # Use expected headers for row comparison
        compare_headers = exp_headers
    else:
        compare_headers = exp_headers

    # Row diff
    if ordered:
        row_diffs = _diff_ordered(exp_rows, act_rows, compare_headers)
    else:
        row_diffs = _diff_unordered(exp_rows, act_rows, compare_headers)

    if row_diffs:
        if not diff_lines:
            diff_lines.append("Tables were not identical:")
        diff_lines.extend(row_diffs)

    if diff_lines:
        output = "\n".join(diff_lines)
        raise TableDiffError(output)


def _normalize_table(
    value: Any,
    role: str,
) -> tuple[list[str], list[dict[str, str]]]:
    """Normalize a diff operand into (headers, rows).

    For ``list[dict]``, headers are the union of all row keys (in
    first-seen order), so a key appearing only in a later row is still
    compared instead of being silently dropped.

    Args:
        value: The data to normalize (table-like, list[dict], or dict).
        role: ``"expected"`` or ``"actual"``, used in error messages.

    Returns:
        A tuple of (headers, list of row dicts).

    Raises:
        ValueError: If value is a list[list] (needs headers).
        TypeError: If value is not a table-like object, list, or dict.
    """
    if isinstance(value, dict):
        value = [value]

    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
        for i, d in enumerate(value):
            if not isinstance(d, dict):
                raise TypeError(
                    f"diff() '{role}' list items must all be dicts, "
                    f"got {type(d).__name__} at index {i}"
                )
        headers = list(dict.fromkeys(k for row in value for k in row))
        return headers, [dict(d) for d in value]

    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], (list, tuple)):
        raise ValueError(
            "Cannot diff list[list] — headers are required. "
            "Provide a table-like object or list[dict] instead."
        )

    if isinstance(value, list) and len(value) == 0:
        return [], []

    if not hasattr(value, "headings") or not hasattr(value, "rows"):
        raise TypeError(
            f"diff() '{role}' must be a table-like object (with 'headings' and 'rows'), "
            f"a list[dict], or a dict — got {type(value).__name__}"
        )

    # Table-like object with headings + rows
    wrapper = TableWrapper(value)
    return list(wrapper.headers), wrapper.as_dicts()


def _cell_str(row: dict[str, str], header: str) -> str:
    """Convert a cell value to string, treating None as empty string."""
    val = row.get(header, "")
    return "" if val is None else str(val)


def _diff_ordered(
    expected: list[dict[str, str]],
    actual: list[dict[str, str]],
    headers: list[str],
) -> list[str]:
    """Compare tables in order and return diff lines if different."""
    diff_lines: list[str] = []
    max_rows = max(len(expected), len(actual))

    for i in range(max_rows):
        if i < len(expected) and i < len(actual):
            exp_vals = [_cell_str(expected[i], h) for h in headers]
            act_vals = [_cell_str(actual[i], h) for h in headers]
            if exp_vals != act_vals:
                diff_lines.append(f"      - {_format_row(exp_vals)}")
                diff_lines.append(f"      + {_format_row(act_vals)}")
        elif i < len(expected):
            exp_vals = [_cell_str(expected[i], h) for h in headers]
            diff_lines.append(f"    - {_format_row(exp_vals)}")
        else:
            act_vals = [_cell_str(actual[i], h) for h in headers]
            diff_lines.append(f"    + {_format_row(act_vals)}")

    return diff_lines


def _diff_unordered(
    expected: list[dict[str, str]],
    actual: list[dict[str, str]],
    headers: list[str],
) -> list[str]:
    """Compare tables ignoring row order and return diff lines if different."""
    exp_tuples = [tuple(_cell_str(row, h) for h in headers) for row in expected]
    act_tuples = [tuple(_cell_str(row, h) for h in headers) for row in actual]

    exp_counter: Counter[tuple[str, ...]] = Counter(exp_tuples)
    act_counter: Counter[tuple[str, ...]] = Counter(act_tuples)

    missing_rows: list[tuple[str, ...]] = []
    for row in sorted(exp_counter):
        diff = exp_counter[row] - act_counter.get(row, 0)
        if diff > 0:
            missing_rows.extend([row] * diff)

    surplus_rows: list[tuple[str, ...]] = []
    for row in sorted(act_counter):
        diff = act_counter[row] - exp_counter.get(row, 0)
        if diff > 0:
            surplus_rows.extend([row] * diff)

    diff_lines: list[str] = []
    for row in missing_rows:
        diff_lines.append(f"    - {_format_row(list(row))}")
    for row in surplus_rows:
        diff_lines.append(f"    + {_format_row(list(row))}")

    return diff_lines


def _format_row(values: list[str]) -> str:
    """Format a single row as a Cucumber-style table row."""
    return f"| {' | '.join(values)} |"
