"""Tests for behave_data.raw_table."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from behave_data.raw_table import RawTable, raw_table


class FakeDictRow:
    """Row whose as_dict() returns keys in a different order than headings."""

    def __init__(self, data: dict[str, str]) -> None:
        self._data = data

    def as_dict(self) -> dict[str, str]:
        return dict(self._data)

    def __getitem__(self, key: str) -> str:
        return self._data[key]


class FakeListRowTable:
    """Table-like object whose rows are plain lists or dict-backed rows."""

    def __init__(self, headings: list[str], rows: list[Any]) -> None:
        self.headings = headings
        self.rows = rows


class TestRowsProperty:
    def test_rows_includes_all_rows(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        """Table with 3 rows: .rows includes all 3 (first row NOT lost)."""
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        assert rt.rows == [["name", "age"], ["Alice", "30"], ["Bob", "25"]]

    def test_rows_preserve_header_order(self) -> None:
        """Regression: as_dict() ordering must not change column alignment."""
        table = FakeListRowTable(["name", "age"], [["Alice", "30"]])
        table.rows = [FakeDictRow({"age": "30", "name": "Alice"})]
        rt = RawTable(table)
        assert rt.rows == [["name", "age"], ["Alice", "30"]]

    def test_rows_from_list_of_lists(self) -> None:
        """Regression: RawTable must support list-of-lists rows."""
        table = FakeListRowTable(["name", "age"], [["Alice", "30"]])
        rt = RawTable(table)
        assert rt.rows == [["name", "age"], ["Alice", "30"]]

    def test_rows_dict_row_missing_header_defaults_to_empty(self) -> None:
        """Regression: missing header in as_dict() must default to '' instead of KeyError."""
        table = FakeListRowTable(["name", "age"], [])
        table.rows = [FakeDictRow({"name": "Alice"})]
        rt = RawTable(table)
        assert rt.rows == [["name", "age"], ["Alice", ""]]

    def test_rows_short_list_row_padded_with_empty_strings(self) -> None:
        """Regression: list row shorter than headings must be padded."""
        table = FakeListRowTable(["name", "age"], [["Alice"]])
        rt = RawTable(table)
        assert rt.rows == [["name", "age"], ["Alice", ""]]

    def test_rows_mapping_without_as_dict_uses_getitem(self) -> None:
        """Regression: custom mapping without as_dict must be read via __getitem__."""

        class CustomMapping:
            def __init__(self, data: dict[str, str]) -> None:
                self._data = data

            def __getitem__(self, key: str) -> str:
                return self._data[key]

        table = FakeListRowTable(["name", "age"], [])
        table.rows = [CustomMapping({"name": "Alice", "age": "30"})]
        rt = RawTable(table)
        assert rt.rows == [["name", "age"], ["Alice", "30"]]

    def test_raw_rows_alias(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        """.raw_rows alias returns same as .rows."""
        table = make_table(["name", "age"], [["Alice", "30"]])
        rt = RawTable(table)
        assert rt.raw_rows == rt.rows

    def test_empty_table(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        """Empty table (0 rows) -> .rows empty, __len__ = 0."""
        table = make_table(["name", "age"], [])
        rt = RawTable(table)
        assert rt.rows == [["name", "age"]]
        assert len(rt) == 1

    def test_one_row(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        """Table with 1 row -> .rows has 1 element (the header)."""
        table = make_table(["value"], [])
        rt = RawTable(table)
        assert len(rt.rows) == 1
        assert rt.rows == [["value"]]

    def test_rows_returns_copy(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        """Immutability: modify copy of .rows -> original unchanged."""
        table = make_table(["name"], [["Alice"]])
        rt = RawTable(table)
        rows = rt.rows
        rows[0][0] = "modified"
        assert rt.rows[0][0] == "name"


class TestToDicts:
    def test_to_dicts_with_custom_headers(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["a", "b"], [["1", "2"], ["3", "4"]])
        rt = RawTable(table)
        result = rt.to_dicts(["col1", "col2"])
        assert result == [
            {"col1": "a", "col2": "b"},
            {"col1": "1", "col2": "2"},
            {"col1": "3", "col2": "4"},
        ]

    def test_to_dicts_headers_longer_than_rows(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        """to_dicts with headers longer than rows -> missing values filled with ''."""
        table = make_table(["a"], [["1"]])
        rt = RawTable(table)
        result = rt.to_dicts(["col1", "col2", "col3"])
        assert result == [
            {"col1": "a", "col2": "", "col3": ""},
            {"col1": "1", "col2": "", "col3": ""},
        ]


class TestToLists:
    def test_to_lists(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        result = rt.to_lists()
        assert result == [["name", "age"], ["Alice", "30"], ["Bob", "25"]]

    def test_to_lists_returns_copy(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name"], [["Alice"]])
        rt = RawTable(table)
        lists = rt.to_lists()
        lists[0][0] = "modified"
        assert rt.to_lists()[0][0] == "name"


class TestLen:
    def test_len_with_data(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        assert len(rt) == 3

    def test_len_empty_data(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name"], [])
        rt = RawTable(table)
        assert len(rt) == 1


class TestGetItem:
    def test_int_index(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name", "age"], [["Alice", "30"]])
        rt = RawTable(table)
        assert rt[0] == ["name", "age"]
        assert rt[1] == ["Alice", "30"]

    def test_int_index_returns_copy(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name"], [["Alice"]])
        rt = RawTable(table)
        row = rt[1]
        row[0] = "modified"
        assert rt[1][0] == "Alice"

    def test_slice(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        result = rt[0:2]
        assert result == [["name", "age"], ["Alice", "30"]]

    def test_slice_returns_copies(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name"], [["Alice"], ["Bob"]])
        rt = RawTable(table)
        result = rt[0:2]
        result[0][0] = "modified"
        assert rt[0][0] == "name"

    def test_out_of_range_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name"], [["Alice"]])
        rt = RawTable(table)
        with pytest.raises(IndexError):
            _ = rt[5]


class TestRepr:
    def test_repr_contains_row_count(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        repr_str = repr(rt)
        assert "RawTable" in repr_str
        assert "rows=3" in repr_str


class TestRawTableFunction:
    def test_returns_raw_table_instance(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name", "age"], [["Alice", "30"]])
        rt = raw_table(table)
        assert isinstance(rt, RawTable)
        assert rt.rows == [["name", "age"], ["Alice", "30"]]


class TestEqualityAndHash:
    def test_equal_same_rows(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name", "age"], [["Alice", "30"]])
        rt1 = RawTable(table)
        rt2 = RawTable(table)
        assert rt1 == rt2

    def test_not_equal_different_rows(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        rt1 = RawTable(make_table(["name"], [["Alice"]]))
        rt2 = RawTable(make_table(["name"], [["Bob"]]))
        assert rt1 != rt2

    def test_not_equal_non_raw_table(self) -> None:
        rt = RawTable(FakeListRowTable(["name"], [["Alice"]]))
        assert rt != "not a raw table"

    def test_hash_raises(self) -> None:
        rt = RawTable(FakeListRowTable(["name"], [["Alice"]]))
        with pytest.raises(TypeError, match="unhashable"):
            hash(rt)
