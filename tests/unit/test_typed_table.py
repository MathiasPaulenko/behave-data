"""Tests for behave_data.typed_table."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any
from unittest.mock import patch

import pytest

from behave_data.config import Config
from behave_data.errors import OptionalDependencyError, TypeConversionError
from behave_data.typed_table import TypedTableWrapper, typed_wrap


class TestCleanHeaders:
    def test_plain_headers(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name", "age"], [["Alice", "30"]])
        tw = TypedTableWrapper(table)
        result = tw.clean_headers()
        assert result == ["name", "age"]

    def test_typed_headers(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name:str", "age:int"], [["Alice", "30"]])
        tw = TypedTableWrapper(table)
        result = tw.clean_headers()
        assert result == ["name", "age"]

    def test_mixed_typed_and_untyped(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name", "age:int", "active:bool"], [])
        tw = TypedTableWrapper(table)
        assert tw.clean_headers() == ["name", "age", "active"]


class TestTypedDicts:
    def test_int_conversion(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["age:int"], [["30"], ["25"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"age": 30}, {"age": 25}]

    def test_float_conversion(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["price:float"], [["3.14"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"price": 3.14}]

    def test_bool_conversion(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["active:bool"], [["true"], ["false"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"active": True}, {"active": False}]

    def test_date_conversion(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["born:date"], [["2024-01-15"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"born": date(2024, 1, 15)}]

    def test_str_conversion(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name:str"], [["Alice"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"name": "Alice"}]

    def test_no_type_returns_string(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name"], [["Alice"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"name": "Alice"}]

    def test_null_markers_empty_cell_to_none(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name"], [[""]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"name": None}]

    def test_null_marker_null_to_none(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int"], [["null"], ["30"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"age": None}, {"age": 30}]

    def test_nullable_type_with_empty_cell(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int?"], [[""], ["30"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"age": None}, {"age": 30}]

    def test_non_nullable_type_empty_cell_still_none(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int"], [[""]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"age": None}]

    def test_whitespace_around_type_colon(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        """Regression: headers like 'age : int?' must be parsed and converted."""
        table = make_table(["name : str", "age : int?"], [["Alice", "30"]])
        tw = TypedTableWrapper(table)
        result = tw.typed_dicts()
        assert result[0] == {"name": "Alice", "age": 30}

    def test_per_column_markers(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["phone", "name"], [["N/A", "Alice"]])
        cfg = Config.from_dict({"null_markers_by_column": {"phone": ["N/A"]}})
        tw = TypedTableWrapper(table, cfg)
        result = tw.typed_dicts()
        assert result[0]["phone"] is None
        assert result[0]["name"] == "Alice"

    def test_without_config_uses_defaults(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name"], [["null"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"name": None}]

    def test_config_override_in_call(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name"], [["<empty>"]])
        tw = TypedTableWrapper(table)
        cfg = Config.from_dict({"null_markers": ["<empty>"]})
        assert tw.typed_dicts(cfg) == [{"name": None}]

    def test_uses_row_get_header_not_positional(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name:str", "age:int"], [["Alice", "30"]])
        tw = TypedTableWrapper(table)
        result = tw.typed_dicts()
        assert result[0] == {"name": "Alice", "age": 30}

    def test_invalid_type_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int"], [["abc"]])
        tw = TypedTableWrapper(table)
        with pytest.raises(TypeConversionError):
            tw.typed_dicts()

    def test_invalid_type_includes_type_name(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int"], [["abc"]])
        tw = TypedTableWrapper(table)
        with pytest.raises(TypeConversionError) as exc_info:
            tw.typed_dicts()
        assert "int" in str(exc_info.value)

    def test_mixed_types(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(
            ["name:str", "age:int", "active:bool"],
            [["Alice", "30", "true"], ["Bob", "25", "false"]],
        )
        tw = TypedTableWrapper(table)
        result = tw.typed_dicts()
        assert result[0] == {"name": "Alice", "age": 30, "active": True}
        assert result[1] == {"name": "Bob", "age": 25, "active": False}

    def test_empty_table(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name:str"], [])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == []

    def test_one_row_one_column(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["value:int"], [["42"]])
        tw = TypedTableWrapper(table)
        assert tw.typed_dicts() == [{"value": 42}]

    def test_type_overrides_apply_when_header_has_no_type(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age", "name"], [["30", "Alice"]])
        cfg = Config.from_dict({"type_overrides": {"age": "int"}})
        tw = TypedTableWrapper(table, cfg)
        assert tw.typed_dicts() == [{"age": 30, "name": "Alice"}]

    def test_type_overrides_nullable_marker(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age", "name"], [["30", "Alice"], ["", "Bob"]])
        cfg = Config.from_dict({"null_markers": ["null"], "type_overrides": {"age": "int?"}})
        tw = TypedTableWrapper(table, cfg)
        assert tw.typed_dicts() == [{"age": 30, "name": "Alice"}, {"age": None, "name": "Bob"}]

    def test_type_overrides_take_priority_over_header_annotation(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int"], [["30"]])
        cfg = Config.from_dict({"type_overrides": {"age": "float"}})
        tw = TypedTableWrapper(table, cfg)
        result = tw.typed_dicts()
        assert isinstance(result[0]["age"], float)
        assert result[0]["age"] == 30.0

    def test_type_overrides_nullable_overrides_header_non_nullable(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int"], [[""], ["30"]])
        cfg = Config.from_dict({"null_markers": [""], "type_overrides": {"age": "int?"}})
        tw = TypedTableWrapper(table, cfg)
        result = tw.typed_dicts()
        assert result[0]["age"] is None
        assert result[1]["age"] == 30

    def test_type_overrides_non_nullable_overrides_header_nullable(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int?"], [[""], ["30"]])
        cfg = Config.from_dict({"null_markers": [""], "type_overrides": {"age": "int"}})
        tw = TypedTableWrapper(table, cfg)
        result = tw.typed_dicts()
        # type_overrides says non-nullable, but null marker still applies
        assert result[0]["age"] is None
        assert result[1]["age"] == 30

    def test_type_overrides_unknown_type_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["price"], [["9.99"]])
        cfg = Config.from_dict({"type_overrides": {"price": "decimal"}})
        tw = TypedTableWrapper(table, cfg)
        with pytest.raises(ValueError, match="Unknown type 'decimal'"):
            tw.typed_dicts()

    def test_type_overrides_empty_type_name_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["price"], [["9.99"]])
        cfg = Config.from_dict({"type_overrides": {"price": "?"}})
        tw = TypedTableWrapper(table, cfg)
        with pytest.raises(ValueError, match="Empty type name"):
            tw.typed_dicts()


class TestTypedObjects:
    def test_dataclass_conversion(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        @dataclass
        class User:
            name: str
            age: int

        table = make_table(["name:str", "age:int"], [["Alice", "30"]])
        tw = TypedTableWrapper(table)
        users = tw.typed_objects(User)
        assert len(users) == 1
        assert users[0].name == "Alice"
        assert users[0].age == 30

    def test_empty_table(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        @dataclass
        class User:
            name: str

        table = make_table(["name:str"], [])
        tw = TypedTableWrapper(table)
        assert tw.typed_objects(User) == []

    def test_pydantic_model(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        pytest.importorskip("pydantic")
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int

        table = make_table(["name:str", "age:int"], [["Alice", "30"]])
        tw = TypedTableWrapper(table)
        users = tw.typed_objects(User)
        assert len(users) == 1
        assert users[0].name == "Alice"
        assert users[0].age == 30


class TestToDict:
    def test_two_columns_key_value(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["key", "value"], [["a", "1"], ["b", "2"]])
        tw = TypedTableWrapper(table)
        result = tw.to_dict()
        assert result == {"a": "1", "b": "2"}

    def test_one_column_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name"], [["Alice"]])
        tw = TypedTableWrapper(table)
        with pytest.raises(ValueError, match="2 columns"):
            tw.to_dict()

    def test_three_columns_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["a", "b", "c"], [["1", "2", "3"]])
        tw = TypedTableWrapper(table)
        with pytest.raises(ValueError, match="2 columns"):
            tw.to_dict()

    def test_typed_columns(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["key:int", "value:float"], [["1", "3.14"], ["2", "2.71"]])
        tw = TypedTableWrapper(table)
        result = tw.to_dict()
        assert result == {1: 3.14, 2: 2.71}

    def test_empty_table(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["key", "value"], [])
        tw = TypedTableWrapper(table)
        assert tw.to_dict() == {}


class TestToLists:
    def test_returns_list_of_lists(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name:str", "age:int"], [["Alice", "30"], ["Bob", "25"]])
        tw = TypedTableWrapper(table)
        result = tw.to_lists()
        assert result == [["Alice", 30], ["Bob", 25]]

    def test_empty_table(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name:str"], [])
        tw = TypedTableWrapper(table)
        assert tw.to_lists() == []


class TestToPandas:
    def test_returns_dataframe(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        pytest.importorskip("pandas")
        table = make_table(["name:str", "age:int"], [["Alice", "30"]])
        tw = TypedTableWrapper(table)
        df = tw.to_pandas()
        assert list(df.columns) == ["name", "age"]
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[0]["age"] == 30

    def test_missing_pandas_raises(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name:str"], [["Alice"]])
        tw = TypedTableWrapper(table)
        with patch.dict(sys.modules, {"pandas": None}):
            with pytest.raises(OptionalDependencyError) as exc_info:
                tw.to_pandas()
            assert "pandas" in str(exc_info.value)


class TestInheritance:
    def test_as_dicts_still_works(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name", "age"], [["Alice", "30"]])
        tw = TypedTableWrapper(table)
        assert tw.as_dicts() == [{"name": "Alice", "age": "30"}]

    def test_transpose_still_works(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name", "age"], [["Alice", "30"]])
        tw = TypedTableWrapper(table)
        transposed = tw.transpose()
        assert transposed is not None

    def test_find_row_still_works(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        tw = TypedTableWrapper(table)
        row = tw.find_row(name="Alice")
        assert row is not None

    def test_headers_still_works(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name:str", "age:int"], [])
        tw = TypedTableWrapper(table)
        assert tw.headers == ["name:str", "age:int"]

    def test_len_still_works(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name"], [["Alice"], ["Bob"]])
        tw = TypedTableWrapper(table)
        assert len(tw) == 2


class TestTypedWrap:
    def test_returns_typed_table_wrapper(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["name:str"], [["Alice"]])
        tw = typed_wrap(table)
        assert isinstance(tw, TypedTableWrapper)
        assert tw.typed_dicts() == [{"name": "Alice"}]

    def test_with_config(self, make_table: Callable[[list[str], list[list[str]]], Any]) -> None:
        table = make_table(["name"], [["<empty>"]])
        cfg = Config.from_dict({"null_markers": ["<empty>"]})
        tw = typed_wrap(table, cfg)
        assert tw.typed_dicts() == [{"name": None}]


class TestTableLikeCompatibility:
    def test_typed_wrapper_exposes_headings_and_rows(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int"], [["30"]])
        tw = typed_wrap(table)
        assert tw.headings == ["age:int"]
        assert tw.rows == [{"age:int": "30"}]

    def test_typed_wrapper_can_rewrap_another_wrapper(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        table = make_table(["age:int"], [["30"]])
        tw = typed_wrap(table)
        chained = TypedTableWrapper(tw)
        assert chained.typed_dicts() == [{"age": 30}]

    def test_raw_table_accepts_typed_wrapper(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        from behave_data import raw_table

        table = make_table(["age:int", "name"], [["30", "Alice"]])
        rt = raw_table(typed_wrap(table))
        assert rt.rows == [["age:int", "name"], ["30", "Alice"]]

    def test_diff_accepts_typed_wrappers(
        self, make_table: Callable[[list[str], list[list[str]]], Any]
    ) -> None:
        from behave_data import diff

        expected = make_table(["age:int"], [["30"]])
        actual = make_table(["age:int"], [["30"]])
        diff(typed_wrap(expected), typed_wrap(actual))
