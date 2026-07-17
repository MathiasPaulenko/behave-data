"""Patch behave.model.Table with behave-data convenience methods."""

from __future__ import annotations

from typing import Any

from behave_data.config import Config
from behave_data.diff import diff as _diff
from behave_data.raw_table import RawTable
from behave_data.typed_table import TypedTableWrapper
from behave_data.typed_table import typed_wrap as _typed_wrap

_ORIGINAL_METHODS: dict[str, Any] = {}
_IS_PATCHED = False

_METHOD_NAMES = [
    "typed_wrap",
    "typed_dicts",
    "typed_objects",
    "clean_headers",
    "to_dict",
    "to_lists",
    "to_pandas",
    "raw_table",
    "diff",
]


def _typed_wrap_method(self: Any, config: Config | None = None) -> TypedTableWrapper:
    return _typed_wrap(self, config)


def _typed_dicts(self: Any, config: Config | None = None) -> list[dict[str, Any]]:
    return TypedTableWrapper(self, config).typed_dicts()


def _typed_objects(self: Any, cls: type, config: Config | None = None) -> list[Any]:
    return TypedTableWrapper(self, config).typed_objects(cls, config)


def _clean_headers(self: Any) -> list[str]:
    return TypedTableWrapper(self).clean_headers()


def _to_dict(self: Any, config: Config | None = None) -> dict[Any, Any]:
    return TypedTableWrapper(self, config).to_dict()


def _to_lists(self: Any, config: Config | None = None) -> list[list[Any]]:
    return TypedTableWrapper(self, config).to_lists()


def _to_pandas(self: Any, config: Config | None = None) -> Any:
    return TypedTableWrapper(self, config).to_pandas()


def _raw_table(self: Any) -> RawTable:
    return RawTable(self)


def _diff_method(
    self: Any,
    other: Any,
    *,
    ordered: bool = True,
    ignore_columns: list[str] | None = None,
    surplus_columns: bool = True,
) -> None:
    _diff(
        self,
        other,
        ordered=ordered,
        ignore_columns=ignore_columns,
        surplus_columns=surplus_columns,
    )


_IMPLEMENTATIONS = {
    "typed_wrap": _typed_wrap_method,
    "typed_dicts": _typed_dicts,
    "typed_objects": _typed_objects,
    "clean_headers": _clean_headers,
    "to_dict": _to_dict,
    "to_lists": _to_lists,
    "to_pandas": _to_pandas,
    "raw_table": _raw_table,
    "diff": _diff_method,
}


def apply_patches() -> None:
    """Add behave-data convenience methods to behave.model.Table.

    This function is idempotent: calling it multiple times has no effect.
    Each method is added as a bound method to the Table class.

    Adds the following methods:
        - typed_wrap(config=None)
        - typed_dicts(config=None)
        - typed_objects(cls, config=None)
        - clean_headers()
        - to_dict(config=None)
        - to_lists(config=None)
        - to_pandas(config=None)
        - raw_table()
        - diff(other, *, ordered=True, ignore_columns=None, surplus_columns=True)

    Sets ``Table._behave_data_patched = True``.
    """
    global _IS_PATCHED
    if _IS_PATCHED:
        return

    try:
        from behave.model import Table
    except ImportError:
        return

    for name in _METHOD_NAMES:
        if hasattr(Table, name):
            _ORIGINAL_METHODS[name] = getattr(Table, name)
        setattr(Table, name, _IMPLEMENTATIONS[name])

    Table._behave_data_patched = True
    _IS_PATCHED = True


def revert_patches() -> None:
    """Restore the original behave.model.Table methods.

    This function is idempotent: calling it when not patched has no effect.
    """
    global _IS_PATCHED
    if not _IS_PATCHED:
        return

    try:
        from behave.model import Table
    except ImportError:
        _ORIGINAL_METHODS.clear()
        _IS_PATCHED = False
        return

    for name in _METHOD_NAMES:
        if name in _ORIGINAL_METHODS:
            setattr(Table, name, _ORIGINAL_METHODS[name])
        else:
            if hasattr(Table, name):
                delattr(Table, name)

    if hasattr(Table, "_behave_data_patched"):
        delattr(Table, "_behave_data_patched")

    _ORIGINAL_METHODS.clear()
    _IS_PATCHED = False
