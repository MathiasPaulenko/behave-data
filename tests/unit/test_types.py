"""Tests for behave_data.types."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from behave_data.errors import TypeConversionError
from behave_data.types import (
    TYPE_CONVERTERS,
    _parse_bool,
    convert_cell,
    parse_column_header,
    register_type,
)


class TestParseBool:
    @pytest.mark.parametrize("value", ["true", "True", "TRUE", "yes", "1", "on"])
    def test_truthy_values(self, value: str) -> None:
        assert _parse_bool(value) is True

    @pytest.mark.parametrize("value", ["false", "False", "FALSE", "no", "0", "off"])
    def test_falsy_values(self, value: str) -> None:
        assert _parse_bool(value) is False

    @pytest.mark.parametrize("value", [1, 1.0, 0, 0.0])
    def test_numeric_bool_values(self, value: float | int) -> None:
        assert _parse_bool(value) is (value == 1)

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse"):
            _parse_bool("maybe")


class TestTypeConverters:
    def test_int(self) -> None:
        assert TYPE_CONVERTERS["int"]("42") == 42

    def test_float(self) -> None:
        assert TYPE_CONVERTERS["float"]("3.14") == 3.14

    def test_str(self) -> None:
        assert TYPE_CONVERTERS["str"]("hello") == "hello"

    def test_bool(self) -> None:
        assert TYPE_CONVERTERS["bool"]("true") is True

    def test_date(self) -> None:
        assert TYPE_CONVERTERS["date"]("2024-01-15") == date(2024, 1, 15)

    def test_datetime(self) -> None:
        result = TYPE_CONVERTERS["datetime"]("2024-01-15T10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_uuid(self) -> None:
        result = TYPE_CONVERTERS["uuid"]("550e8400-e29b-41d4-a716-446655440000")
        assert result == UUID("550e8400-e29b-41d4-a716-446655440000")

    def test_json(self) -> None:
        assert TYPE_CONVERTERS["json"]('{"key": "value"}') == {"key": "value"}


class TestRegisterType:
    def test_registers_custom_type(self) -> None:
        register_type("decimal", Decimal)
        assert "decimal" in TYPE_CONVERTERS
        assert TYPE_CONVERTERS["decimal"]("3.14") == Decimal("3.14")
        del TYPE_CONVERTERS["decimal"]

    def test_overrides_existing_type(self) -> None:
        original = TYPE_CONVERTERS["int"]
        register_type("int", lambda x: int(x) * 2)
        assert TYPE_CONVERTERS["int"]("5") == 10
        TYPE_CONVERTERS["int"] = original


class TestParseColumnHeader:
    def test_plain_header_no_type(self) -> None:
        name, converter, nullable = parse_column_header("name")
        assert name == "name"
        assert converter is None
        assert nullable is False

    def test_header_with_known_type(self) -> None:
        name, converter, nullable = parse_column_header("doors:int")
        assert name == "doors"
        assert converter is int
        assert nullable is False

    def test_header_with_nullable_type(self) -> None:
        name, converter, nullable = parse_column_header("price:float?")
        assert name == "price"
        assert converter is float
        assert nullable is True

    def test_header_with_unknown_type_returns_literal(self) -> None:
        name, converter, nullable = parse_column_header("url:https://x")
        assert name == "url:https://x"
        assert converter is None
        assert nullable is False

    def test_header_with_colon_in_name_unknown_type(self) -> None:
        name, converter, nullable = parse_column_header("url:https://example.com")
        assert name == "url:https://example.com"
        assert converter is None
        assert nullable is False

    def test_empty_string(self) -> None:
        name, converter, nullable = parse_column_header("")
        assert name == ""
        assert converter is None
        assert nullable is False

    def test_only_colon(self) -> None:
        name, converter, nullable = parse_column_header(":")
        assert name == ""
        assert converter is None
        assert nullable is False

    def test_str_type(self) -> None:
        name, converter, nullable = parse_column_header("label:str")
        assert name == "label"
        assert converter is str
        assert nullable is False

    def test_bool_type(self) -> None:
        name, converter, nullable = parse_column_header("active:bool")
        assert name == "active"
        assert converter is not None
        assert converter("true") is True
        assert nullable is False

    def test_nullable_str_type(self) -> None:
        name, converter, nullable = parse_column_header("note:str?")
        assert name == "note"
        assert converter is str
        assert nullable is True

    def test_custom_registered_type(self) -> None:
        register_type("decimal", Decimal)
        name, converter, nullable = parse_column_header("price:decimal")
        assert name == "price"
        assert converter is Decimal
        assert nullable is False
        del TYPE_CONVERTERS["decimal"]

    def test_nullable_unknown_type_returns_literal(self) -> None:
        name, converter, nullable = parse_column_header("data:unknown?")
        assert name == "data:unknown?"
        assert converter is None
        assert nullable is False

    def test_whitespace_around_colon_is_stripped(self) -> None:
        name, converter, nullable = parse_column_header("age : int?")
        assert name == "age"
        assert converter is int
        assert nullable is True

    def test_whitespace_before_type_name_is_stripped(self) -> None:
        name, converter, nullable = parse_column_header("name :  str")
        assert name == "name"
        assert converter is str
        assert nullable is False

    def test_nullable_empty_type_preserves_flag(self) -> None:
        """Regression: name:? should return nullable=True, not False."""
        name, converter, nullable = parse_column_header("name:?")
        assert name == "name"
        assert converter is None
        assert nullable is True

    def test_only_colon_with_question_mark(self) -> None:
        """Regression: :? should return nullable=True, not False."""
        name, converter, nullable = parse_column_header(":?")
        assert name == ""
        assert converter is None
        assert nullable is True


class TestConvertCell:
    def test_converter_none_returns_value(self) -> None:
        assert convert_cell("hello", None) == "hello"

    def test_convert_int(self) -> None:
        assert convert_cell("42", int) == 42

    def test_convert_float(self) -> None:
        assert convert_cell("3.14", float) == 3.14

    def test_convert_bool_true(self) -> None:
        from behave_data.types import _parse_bool

        assert convert_cell("true", _parse_bool) is True

    def test_convert_bool_false(self) -> None:
        from behave_data.types import _parse_bool

        assert convert_cell("false", _parse_bool) is False

    def test_convert_str(self) -> None:
        assert convert_cell("hello", str) == "hello"

    def test_convert_date(self) -> None:
        from behave_data.types import _parse_date

        assert convert_cell("2024-01-15", _parse_date) == date(2024, 1, 15)

    def test_convert_datetime(self) -> None:
        from behave_data.types import _parse_datetime

        assert convert_cell("2024-01-15T10:30:00", _parse_datetime) == datetime(2024, 1, 15, 10, 30)

    def test_convert_uuid(self) -> None:
        from behave_data.types import _parse_uuid

        result = convert_cell("550e8400-e29b-41d4-a716-446655440000", _parse_uuid)
        assert isinstance(result, UUID)

    def test_convert_json(self) -> None:
        from behave_data.types import _parse_json

        assert convert_cell('{"a": 1}', _parse_json) == {"a": 1}

    def test_convert_with_column_name_in_error(self) -> None:
        with pytest.raises(TypeConversionError) as exc_info:
            convert_cell("abc", int, column_name="doors", type_name="int")
        assert exc_info.value.column == "doors"

    def test_convert_failed_raises_type_conversion_error(self) -> None:
        with pytest.raises(TypeConversionError) as exc_info:
            convert_cell("abc", int, column_name="age", type_name="int")
        assert exc_info.value.column == "age"
        assert exc_info.value.value == "abc"
        assert exc_info.value.target_type == "int"

    def test_convert_invalid_bool_raises(self) -> None:
        from behave_data.types import _parse_bool

        with pytest.raises(TypeConversionError):
            convert_cell("maybe", _parse_bool)

    def test_convert_invalid_date_raises(self) -> None:
        from behave_data.types import _parse_date

        with pytest.raises(TypeConversionError):
            convert_cell("not-a-date", _parse_date)

    def test_convert_invalid_uuid_raises(self) -> None:
        from behave_data.types import _parse_uuid

        with pytest.raises(TypeConversionError):
            convert_cell("not-a-uuid", _parse_uuid)

    def test_convert_bool_from_native_bool(self) -> None:
        from behave_data.types import _parse_bool

        assert convert_cell(True, _parse_bool) is True
        assert convert_cell(False, _parse_bool) is False

    def test_convert_date_from_datetime(self) -> None:
        from behave_data.types import _parse_date

        assert convert_cell(datetime(2024, 1, 15, 10, 30), _parse_date) == date(2024, 1, 15)

    def test_convert_datetime_from_date(self) -> None:
        from behave_data.types import _parse_datetime

        assert convert_cell(date(2024, 1, 15), _parse_datetime) == datetime(2024, 1, 15, 0, 0)

    def test_convert_datetime_from_datetime(self) -> None:
        from behave_data.types import _parse_datetime

        dt = datetime(2024, 1, 15, 10, 30)
        assert convert_cell(dt, _parse_datetime) is dt

    def test_convert_uuid_from_uuid(self) -> None:
        import uuid

        from behave_data.types import _parse_uuid

        u = uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert convert_cell(u, _parse_uuid) is u

    def test_convert_json_from_parsed_object(self) -> None:
        from behave_data.types import _parse_json

        data = {"a": 1}
        assert convert_cell(data, _parse_json) is data

    def test_convert_invalid_json_raises(self) -> None:
        from behave_data.types import _parse_json

        with pytest.raises(TypeConversionError):
            convert_cell("{invalid", _parse_json)

    def test_convert_preserves_cause(self) -> None:
        with pytest.raises(TypeConversionError) as exc_info:
            convert_cell("abc", int, column_name="age", type_name="int")
        assert isinstance(exc_info.value.cause, ValueError)
