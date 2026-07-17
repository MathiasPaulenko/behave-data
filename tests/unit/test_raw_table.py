"""Tests for behave_data.raw_table."""

from __future__ import annotations

import pytest

from behave_data.raw_table import RawTable, raw_table


class TestRowsProperty:
    def test_rows_includes_all_rows(self, make_table: object) -> None:
        """Table with 3 rows: .rows includes all 3 (first row NOT lost)."""
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        assert rt.rows == [["name", "age"], ["Alice", "30"], ["Bob", "25"]]

    def test_raw_rows_alias(self, make_table: object) -> None:
        """.raw_rows alias returns same as .rows."""
        table = make_table(["name", "age"], [["Alice", "30"]])
        rt = RawTable(table)
        assert rt.raw_rows == rt.rows

    def test_empty_table(self, make_table: object) -> None:
        """Empty table (0 rows) -> .rows empty, __len__ = 0."""
        table = make_table(["name", "age"], [])
        rt = RawTable(table)
        assert rt.rows == [["name", "age"]]
        assert len(rt) == 1

    def test_one_row(self, make_table: object) -> None:
        """Table with 1 row -> .rows has 1 element (the header)."""
        table = make_table(["value"], [])
        rt = RawTable(table)
        assert len(rt.rows) == 1
        assert rt.rows == [["value"]]

    def test_rows_returns_copy(self, make_table: object) -> None:
        """Immutability: modify copy of .rows -> original unchanged."""
        table = make_table(["name"], [["Alice"]])
        rt = RawTable(table)
        rows = rt.rows
        rows[0][0] = "modified"
        assert rt.rows[0][0] == "name"


class TestToDicts:
    def test_to_dicts_with_custom_headers(self, make_table: object) -> None:
        table = make_table(["a", "b"], [["1", "2"], ["3", "4"]])
        rt = RawTable(table)
        result = rt.to_dicts(["col1", "col2"])
        assert result == [
            {"col1": "a", "col2": "b"},
            {"col1": "1", "col2": "2"},
            {"col1": "3", "col2": "4"},
        ]

    def test_to_dicts_headers_longer_than_rows(self, make_table: object) -> None:
        """to_dicts with headers longer than rows -> missing values filled with ''."""
        table = make_table(["a"], [["1"]])
        rt = RawTable(table)
        result = rt.to_dicts(["col1", "col2", "col3"])
        assert result == [
            {"col1": "a", "col2": "", "col3": ""},
            {"col1": "1", "col2": "", "col3": ""},
        ]


class TestToLists:
    def test_to_lists(self, make_table: object) -> None:
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        result = rt.to_lists()
        assert result == [["name", "age"], ["Alice", "30"], ["Bob", "25"]]

    def test_to_lists_returns_copy(self, make_table: object) -> None:
        table = make_table(["name"], [["Alice"]])
        rt = RawTable(table)
        lists = rt.to_lists()
        lists[0][0] = "modified"
        assert rt.to_lists()[0][0] == "name"


class TestLen:
    def test_len_with_data(self, make_table: object) -> None:
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        assert len(rt) == 3

    def test_len_empty_data(self, make_table: object) -> None:
        table = make_table(["name"], [])
        rt = RawTable(table)
        assert len(rt) == 1


class TestGetItem:
    def test_int_index(self, make_table: object) -> None:
        table = make_table(["name", "age"], [["Alice", "30"]])
        rt = RawTable(table)
        assert rt[0] == ["name", "age"]
        assert rt[1] == ["Alice", "30"]

    def test_int_index_returns_copy(self, make_table: object) -> None:
        table = make_table(["name"], [["Alice"]])
        rt = RawTable(table)
        row = rt[1]
        row[0] = "modified"
        assert rt[1][0] == "Alice"

    def test_slice(self, make_table: object) -> None:
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        result = rt[0:2]
        assert result == [["name", "age"], ["Alice", "30"]]

    def test_slice_returns_copies(self, make_table: object) -> None:
        table = make_table(["name"], [["Alice"], ["Bob"]])
        rt = RawTable(table)
        result = rt[0:2]
        result[0][0] = "modified"
        assert rt[0][0] == "name"

    def test_out_of_range_raises(self, make_table: object) -> None:
        table = make_table(["name"], [["Alice"]])
        rt = RawTable(table)
        with pytest.raises(IndexError):
            _ = rt[5]


class TestRepr:
    def test_repr_contains_row_count(self, make_table: object) -> None:
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        rt = RawTable(table)
        repr_str = repr(rt)
        assert "RawTable" in repr_str
        assert "rows=3" in repr_str


class TestRawTableFunction:
    def test_returns_raw_table_instance(self, make_table: object) -> None:
        table = make_table(["name", "age"], [["Alice", "30"]])
        rt = raw_table(table)
        assert isinstance(rt, RawTable)
        assert rt.rows == [["name", "age"], ["Alice", "30"]]
