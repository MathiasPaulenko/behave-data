"""Tests for behave_data.diff."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import pytest

from behave_data.diff import diff
from behave_data.errors import TableDiffError


class TestIdenticalTables:
    def test_identical_tables_no_error(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        actual = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        diff(expected, actual)

    def test_single_row_identical(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        actual = make_table(["name"], [["Alice"]])
        diff(expected, actual)

    def test_both_empty_same_headers_no_error(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [])
        actual = make_table(["name", "age"], [])
        diff(expected, actual)


class TestOrderedDiff:
    def test_different_tables_ordered_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        actual = make_table(["name", "age"], [["Alice", "31"], ["Bob", "25"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual)
        output = str(exc_info.value)
        assert "Tables were not identical" in output
        assert "-" in output
        assert "+" in output

    def test_row_order_matters(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"], ["Bob"]])
        actual = make_table(["name"], [["Bob"], ["Alice"]])
        with pytest.raises(TableDiffError):
            diff(expected, actual)

    def test_missing_row_in_actual(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"], ["Bob"]])
        actual = make_table(["name"], [["Alice"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual)
        output = str(exc_info.value)
        assert "-" in output
        assert "Bob" in output

    def test_surplus_row_in_actual(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        actual = make_table(["name"], [["Alice"], ["Bob"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual)
        output = str(exc_info.value)
        assert "+" in output
        assert "Bob" in output


class TestUnorderedDiff:
    def test_duplicate_rows_preserved_in_unordered_diff(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"], ["Alice"]])
        actual = make_table(["name"], [["Alice"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual, ordered=False)
        output = str(exc_info.value)
        assert "Alice" in output
        assert output.count("-") == 1

    def test_order_doesnt_matter(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"], ["Bob"]])
        actual = make_table(["name"], [["Bob"], ["Alice"]])
        diff(expected, actual, ordered=False)

    def test_different_data_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"], ["Bob"]])
        actual = make_table(["name"], [["Alice"], ["Charlie"]])
        with pytest.raises(TableDiffError):
            diff(expected, actual, ordered=False)

    def test_missing_row_in_actual_unordered(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"], ["Bob"]])
        actual = make_table(["name"], [["Alice"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual, ordered=False)
        output = str(exc_info.value)
        assert "-" in output
        assert "Bob" in output

    def test_surplus_row_in_actual_unordered(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        actual = make_table(["name"], [["Alice"], ["Bob"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual, ordered=False)
        output = str(exc_info.value)
        assert "+" in output
        assert "Bob" in output


class TestIgnoreColumns:
    def test_ignored_column_not_compared(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [["Alice", "30"]])
        actual = make_table(["name", "age"], [["Alice", "99"]])
        diff(expected, actual, ignore_columns=["age"])

    def test_ignored_column_allows_different_values(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age", "city"], [["Alice", "30", "NYC"]])
        actual = make_table(["name", "age", "city"], [["Alice", "25", "LA"]])
        diff(expected, actual, ignore_columns=["age", "city"])

    def test_ignore_nonexistent_column_no_error(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        actual = make_table(["name"], [["Alice"]])
        diff(expected, actual, ignore_columns=["nonexistent"])


class TestSurplusColumns:
    def test_surplus_columns_false_ignores_extra(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        actual = make_table(["name", "age"], [["Alice", "30"]])
        diff(expected, actual, surplus_columns=False)

    def test_surplus_columns_true_raises_on_extra(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        actual = make_table(["name", "age"], [["Alice", "30"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual, surplus_columns=True)
        assert "Headers differ" in str(exc_info.value)


class TestDifferentHeaders:
    def test_different_headers_includes_header_diff(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [["Alice", "30"]])
        actual = make_table(["name", "years"], [["Alice", "30"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual)
        assert "Headers differ" in str(exc_info.value)

    def test_missing_column_in_actual(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [["Alice", "30"]])
        actual = make_table(["name"], [["Alice"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual)
        assert "Headers differ" in str(exc_info.value)


class TestActualEmpty:
    def test_actual_empty_all_expected_shown_as_minus(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"], ["Bob"]])
        actual = make_table(["name"], [])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual)
        output = str(exc_info.value)
        assert "-" in output
        assert "Alice" in output
        assert "Bob" in output


class TestExpectedEmpty:
    def test_expected_empty_all_actual_shown_as_plus(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [])
        actual = make_table(["name"], [["Alice"], ["Bob"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual)
        output = str(exc_info.value)
        assert "+" in output
        assert "Alice" in output
        assert "Bob" in output


class TestActualAsListDict:
    def test_actual_as_list_of_dicts(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [["Alice", "30"]])
        actual = [{"name": "Alice", "age": "30"}]
        diff(expected, actual)

    def test_actual_as_list_of_dicts_different_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [["Alice", "30"]])
        actual = [{"name": "Alice", "age": "31"}]
        with pytest.raises(TableDiffError):
            diff(expected, actual)


class TestActualAsListList:
    def test_actual_as_list_of_lists_raises_value_error(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [["Alice", "30"]])
        actual = [["Alice", "30"]]
        with pytest.raises(ValueError, match="headers are required"):
            diff(expected, actual)


class TestActualAsDict:
    def test_actual_as_single_dict_wrapped(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name", "age"], [["Alice", "30"]])
        actual = {"name": "Alice", "age": "30"}
        diff(expected, actual)


class TestMixedTypes:
    def test_mixed_types_marked_in_diff(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["active"], [["true"]])
        actual = make_table(["active"], cast(list[list[str]], [[True]]))
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual)
        output = str(exc_info.value)
        assert "-" in output
        assert "+" in output


class TestTableDiffError:
    def test_catchable_as_assertion_error(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        actual = make_table(["name"], [["Bob"]])
        with pytest.raises(AssertionError):
            diff(expected, actual)

    def test_has_diff_output_attribute(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        actual = make_table(["name"], [["Bob"]])
        with pytest.raises(TableDiffError) as exc_info:
            diff(expected, actual)
        assert hasattr(exc_info.value, "diff_output")
        assert isinstance(exc_info.value.diff_output, str)
        assert "Tables were not identical" in exc_info.value.diff_output


class TestDiffNoneHandling:
    """Regression tests for None value handling in diff."""

    def test_none_in_actual_dict_treated_as_empty(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        """None values in list[dict] actual should match empty cells in expected."""
        expected = make_table(["name", "age"], [["Alice", ""]])
        actual = [{"name": "Alice", "age": None}]
        diff(expected, actual)  # should not raise

    def test_none_does_not_match_string_none(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        """None value should NOT match the string 'None' in expected."""
        expected = make_table(["name"], [["None"]])
        actual = [{"name": None}]
        with pytest.raises(TableDiffError):
            diff(expected, actual)

    def test_none_in_unordered_diff(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        """None values should be treated as empty in unordered diff."""
        expected = make_table(["name", "age"], [["Alice", ""], ["Bob", "30"]])
        actual = [{"name": "Bob", "age": "30"}, {"name": "Alice", "age": None}]
        diff(expected, actual, ordered=False)  # should not raise


class TestUnsupportedActualTypes:
    """Regression tests for clear TypeError on unsupported actual types."""

    def test_none_actual_raises_type_error(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        with pytest.raises(TypeError, match="must be a table-like object"):
            diff(expected, None)

    def test_int_actual_raises_type_error(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        with pytest.raises(TypeError, match="must be a table-like object"):
            diff(expected, 42)

    def test_str_actual_raises_type_error(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        expected = make_table(["name"], [["Alice"]])
        with pytest.raises(TypeError, match="must be a table-like object"):
            diff(expected, "hello")
