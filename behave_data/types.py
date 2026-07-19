"""Type conversion for behave-data table cells."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from behave_data.errors import TypeConversionError

ConverterFn = Callable[[Any], Any]


def _parse_bool(value: Any) -> bool:
    """Parse a value to bool.

    Accepts native bools, numeric 0/1, and common string representations.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in ("true", "yes", "1", "on"):
        return True
    if lowered in ("false", "no", "0", "off"):
        return False
    raise ValueError(f"Cannot parse {value!r} as bool")


def _parse_date(value: Any) -> date:
    """Parse a value to date (ISO format: YYYY-MM-DD)."""
    if isinstance(value, date):
        return value.date() if isinstance(value, datetime) else value
    return date.fromisoformat(str(value).strip())


def _parse_datetime(value: Any) -> datetime:
    """Parse a value to datetime (ISO format)."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return datetime.fromisoformat(str(value).strip())


def _parse_uuid(value: Any) -> uuid.UUID:
    """Parse a value to UUID."""
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value).strip())


def _parse_json(value: Any) -> Any:
    """Parse a string as JSON, or return already-parsed data unchanged."""
    if isinstance(value, str):
        return json.loads(value)
    return value


TYPE_CONVERTERS: dict[str, ConverterFn] = {
    "int": int,
    "float": float,
    "bool": _parse_bool,
    "str": str,
    "date": _parse_date,
    "datetime": _parse_datetime,
    "uuid": _parse_uuid,
    "json": _parse_json,
}


def register_type(name: str, converter: ConverterFn) -> None:
    """Register a custom type converter.

    Args:
        name: The type name to register (e.g. ``"decimal"``).
        converter: A function that takes a string and returns the converted value.
    """
    TYPE_CONVERTERS[name] = converter


def parse_column_header(header: str) -> tuple[str, ConverterFn | None, bool]:
    """Extract the column name, converter, and nullable flag from a header.

    Headers use colon-separated type annotations with optional ``?`` suffix
    for nullable columns:

        ``"name"``       -> ``("name", None, False)``
        ``"doors:int"``  -> ``("doors", int, False)``
        ``"price:float?"`` -> ``("price", float, True)``

    If the type name is not registered in ``TYPE_CONVERTERS``, the entire
    header is treated as a literal column name:

        ``"url:https://x"`` -> ``("url:https://x", None, False)``

    Args:
        header: The raw header string.

    Returns:
        A tuple of (column_name, converter_or_None, nullable_flag).
    """
    if ":" not in header:
        return header, None, False

    name, type_part = header.rsplit(":", 1)
    name = name.strip()
    type_part = type_part.strip()

    nullable = False
    if type_part.endswith("?"):
        nullable = True
        type_part = type_part[:-1].strip()

    if type_part == "":
        return name, None, nullable

    converter = TYPE_CONVERTERS.get(type_part)
    if converter is None:
        return header, None, False

    return name, converter, nullable


def convert_cell(
    value: Any,
    converter: ConverterFn | None,
    column_name: str = "",
    type_name: str = "",
) -> Any:
    """Convert a cell value using the given converter.

    Args:
        value: The cell value to convert.
        converter: The converter callable, or None to return value unchanged.
        column_name: The column name for error reporting.
        type_name: The type name for error reporting.

    Returns:
        The converted value, or the original value if converter is None.

    Raises:
        TypeConversionError: If the conversion fails.
    """
    if converter is None:
        return value
    try:
        return converter(value)
    except Exception as exc:
        raise TypeConversionError(column_name, value, type_name, exc) from exc
