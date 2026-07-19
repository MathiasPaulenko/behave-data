"""Tests for behave_data.null."""

from __future__ import annotations

from behave_data.config import Config
from behave_data.null import get_column_markers, is_null, resolve_null


class TestIsNull:
    def test_empty_string_is_null_with_defaults(self) -> None:
        assert is_null("") is True

    def test_null_is_null_with_defaults(self) -> None:
        assert is_null("null") is True

    def test_n_a_is_null_with_defaults(self) -> None:
        assert is_null("N/A") is True

    def test_none_is_null_with_defaults(self) -> None:
        assert is_null("None") is True

    def test_alice_is_not_null(self) -> None:
        assert is_null("Alice") is False

    def test_whitespace_is_not_null(self) -> None:
        assert is_null("  ") is False

    def test_custom_markers_empty_is_null(self) -> None:
        markers = frozenset({"EMPTY"})
        assert is_null("EMPTY", markers=markers) is True

    def test_custom_markers_default_not_null(self) -> None:
        markers = frozenset({"EMPTY"})
        assert is_null("null", markers=markers) is False

    def test_per_column_markers_null_for_phone(self) -> None:
        column_markers = frozenset({"N/A"})
        assert is_null("N/A", column_markers=column_markers) is True

    def test_per_column_markers_not_null_for_email(self) -> None:
        markers = frozenset({"null"})
        column_markers = frozenset({"N/A"})
        assert is_null("N/A", markers=markers, column_markers=column_markers) is True
        assert is_null("null", markers=markers, column_markers=column_markers) is False

    def test_priority_column_markers_over_global(self) -> None:
        markers = frozenset({"null", "N/A"})
        column_markers = frozenset({"missing"})
        assert is_null("missing", markers=markers, column_markers=column_markers) is True
        assert is_null("null", markers=markers, column_markers=column_markers) is False

    def test_empty_markers_nothing_is_null(self) -> None:
        markers: frozenset[str] = frozenset()
        assert is_null("", markers=markers) is False
        assert is_null("null", markers=markers) is False


class TestResolveNull:
    def test_resolves_null_to_none(self) -> None:
        assert resolve_null("") is None
        assert resolve_null("null") is None
        assert resolve_null("N/A") is None

    def test_returns_non_null_value(self) -> None:
        assert resolve_null("Alice") == "Alice"

    def test_with_custom_markers(self) -> None:
        markers = frozenset({"EMPTY"})
        assert resolve_null("EMPTY", markers=markers) is None
        assert resolve_null("null", markers=markers) == "null"

    def test_with_column_markers(self) -> None:
        markers = frozenset({"null"})
        column_markers = frozenset({"N/A"})
        assert resolve_null("N/A", markers=markers, column_markers=column_markers) is None
        assert resolve_null("null", markers=markers, column_markers=column_markers) == "null"


class TestGetColumnMarkers:
    def test_returns_markers_for_known_column(self) -> None:
        cfg = Config.from_dict({"null_markers_by_column": {"phone": ["N/A"]}})
        markers = get_column_markers("phone", cfg)
        assert markers == frozenset({"N/A"})

    def test_returns_none_for_unknown_column(self) -> None:
        cfg = Config.from_dict({"null_markers_by_column": {"phone": ["N/A"]}})
        markers = get_column_markers("email", cfg)
        assert markers is None

    def test_returns_none_when_no_column_markers(self) -> None:
        cfg = Config()
        markers = get_column_markers("any", cfg)
        assert markers is None
