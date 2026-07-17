"""Null handling for behave-data table cells."""

from __future__ import annotations

from behave_data.config import DEFAULT_NULL_MARKERS, Config


def get_column_markers(column_name: str, config: Config) -> frozenset[str] | None:
    """Get the per-column null markers for a specific column.

    Args:
        column_name: The column name.
        config: The Config to query.

    Returns:
        A frozenset of null markers for the column, or None if no
        per-column markers are defined.
    """
    return config.null_markers_by_column.get(column_name)


def is_null(
    value: str,
    markers: frozenset[str] | None = None,
    column_markers: frozenset[str] | None = None,
) -> bool:
    """Check if a value is a null marker.

    Priority: ``column_markers`` > ``markers`` > ``DEFAULT_NULL_MARKERS``.

    Args:
        value: The string value to check.
        markers: Global null markers. If None, defaults are used.
        column_markers: Per-column markers that override global markers.

    Returns:
        True if the value is a null marker, False otherwise.
    """
    if column_markers is not None:
        return value in column_markers
    if markers is not None:
        return value in markers
    return value in DEFAULT_NULL_MARKERS


def resolve_null(
    value: str,
    markers: frozenset[str] | None = None,
    column_markers: frozenset[str] | None = None,
) -> str | None:
    """Resolve a null marker to None, or return the value unchanged.

    Priority: ``column_markers`` > ``markers`` > ``DEFAULT_NULL_MARKERS``.

    Args:
        value: The string value to resolve.
        markers: Global null markers. If None, defaults are used.
        column_markers: Per-column markers that override global markers.

    Returns:
        None if the value is a null marker, otherwise the original value.
    """
    if is_null(value, markers, column_markers):
        return None
    return value
