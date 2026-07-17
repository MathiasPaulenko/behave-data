"""Tests for behave_data.patch."""

from __future__ import annotations

import sys

import pytest

from behave_data.patch import apply_patches, revert_patches


class FakeTable:
    """Minimal fake Table for patch testing."""

    def __init__(self, headings: list[str], rows: list[list[str]]) -> None:
        self.headings = headings
        self.rows = [FakeRow(dict(zip(headings, r, strict=False))) for r in rows]


class FakeRow:
    def __init__(self, data: dict[str, str]) -> None:
        self._data = data

    def as_dict(self) -> dict[str, str]:
        return dict(self._data)

    def __getitem__(self, key: str) -> str:
        return self._data[key]


@pytest.fixture
def patched_table_cls(monkeypatch: pytest.MonkeyPatch) -> type[FakeTable]:
    """Patch FakeTable as if it were behave.model.Table."""
    revert_patches()
    monkeypatch.setattr("behave.model.Table", FakeTable, raising=False)
    apply_patches()
    yield FakeTable
    revert_patches()


class TestApplyPatches:
    def test_methods_added(self, patched_table_cls: type) -> None:
        assert hasattr(patched_table_cls, "typed_wrap")
        assert hasattr(patched_table_cls, "typed_dicts")
        assert hasattr(patched_table_cls, "typed_objects")
        assert hasattr(patched_table_cls, "clean_headers")
        assert hasattr(patched_table_cls, "to_dict")
        assert hasattr(patched_table_cls, "to_lists")
        assert hasattr(patched_table_cls, "to_pandas")
        assert hasattr(patched_table_cls, "raw_table")
        assert hasattr(patched_table_cls, "diff")

    def test_patched_flag_set(self, patched_table_cls: type) -> None:
        assert getattr(patched_table_cls, "_behave_data_patched", False) is True

    def test_typed_wrap_works(self, patched_table_cls: type) -> None:
        from behave_data.typed_table import TypedTableWrapper

        table = patched_table_cls(["name:str", "age:int"], [["Alice", "30"]])
        tw = table.typed_wrap()
        assert isinstance(tw, TypedTableWrapper)
        assert tw.typed_dicts() == [{"name": "Alice", "age": 30}]

    def test_typed_dicts_delegates_correctly(self, patched_table_cls: type) -> None:
        table = patched_table_cls(["name:str", "age:int"], [["Alice", "30"]])
        result = table.typed_dicts()
        assert result == [{"name": "Alice", "age": 30}]

    def test_clean_headers_works(self, patched_table_cls: type) -> None:
        table = patched_table_cls(["name:str", "age:int"], [])
        result = table.clean_headers()
        assert result == ["name", "age"]

    def test_raw_table_works(self, patched_table_cls: type) -> None:
        table = patched_table_cls(["name"], [["Alice"]])
        rt = table.raw_table()
        assert rt.rows == [["name"], ["Alice"]]
        assert len(rt) == 2

    def test_diff_works(self, patched_table_cls: type) -> None:
        table1 = patched_table_cls(["name"], [["Alice"]])
        table2 = patched_table_cls(["name"], [["Bob"]])
        from behave_data.errors import TableDiffError

        with pytest.raises(TableDiffError):
            table1.diff(table2)

    def test_typed_objects_works(self, patched_table_cls: type) -> None:
        from dataclasses import dataclass

        @dataclass
        class User:
            name: str
            age: int

        table = patched_table_cls(["name:str", "age:int"], [["Alice", "30"]])
        users = table.typed_objects(User)
        assert len(users) == 1
        assert users[0].name == "Alice"
        assert users[0].age == 30

    def test_to_dict_works(self, patched_table_cls: type) -> None:
        table = patched_table_cls(["key:str", "value:int"], [["a", "1"], ["b", "2"]])
        result = table.to_dict()
        assert result == {"a": 1, "b": 2}

    def test_to_lists_works(self, patched_table_cls: type) -> None:
        table = patched_table_cls(["name:str", "age:int"], [["Alice", "30"], ["Bob", "25"]])
        result = table.to_lists()
        assert result == [["Alice", 30], ["Bob", 25]]

    def test_to_pandas_raises_without_pandas(
        self, patched_table_cls: type, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        table = patched_table_cls(["name:str"], [["Alice"]])
        from behave_data.errors import OptionalDependencyError

        monkeypatch.setitem(sys.modules, "pandas", None)
        with pytest.raises(OptionalDependencyError):
            table.to_pandas()


class TestIdempotence:
    def test_apply_twice_no_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        revert_patches()
        monkeypatch.setattr("behave.model.Table", FakeTable, raising=False)
        apply_patches()
        apply_patches()
        assert hasattr(FakeTable, "typed_dicts")
        revert_patches()

    def test_revert_twice_no_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        revert_patches()
        monkeypatch.setattr("behave.model.Table", FakeTable, raising=False)
        apply_patches()
        revert_patches()
        revert_patches()


class TestRevertPatches:
    def test_methods_removed_after_revert(self, monkeypatch: pytest.MonkeyPatch) -> None:
        revert_patches()
        monkeypatch.setattr("behave.model.Table", FakeTable, raising=False)
        apply_patches()
        assert hasattr(FakeTable, "typed_dicts")
        revert_patches()
        assert not hasattr(FakeTable, "typed_dicts")

    def test_original_methods_restored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        revert_patches()

        def original(self: object) -> str:
            return "original"

        FakeTable.existing_method = original
        monkeypatch.setattr("behave.model.Table", FakeTable, raising=False)

        from behave_data.patch import _IMPLEMENTATIONS

        monkeypatch.setitem(_IMPLEMENTATIONS, "existing_method", lambda self: "patched")
        monkeypatch.setattr("behave_data.patch._METHOD_NAMES", ["existing_method"])

        apply_patches()
        assert FakeTable.existing_method(FakeTable([], [])) == "patched"
        revert_patches()
        assert FakeTable.existing_method(FakeTable([], [])) == "original"

        del FakeTable.existing_method

    def test_new_methods_deleted_on_revert(self, monkeypatch: pytest.MonkeyPatch) -> None:
        revert_patches()
        monkeypatch.setattr("behave.model.Table", FakeTable, raising=False)
        apply_patches()
        assert hasattr(FakeTable, "typed_dicts")
        revert_patches()
        assert not hasattr(FakeTable, "typed_dicts")

    def test_patched_flag_removed_on_revert(self, monkeypatch: pytest.MonkeyPatch) -> None:
        revert_patches()
        monkeypatch.setattr("behave.model.Table", FakeTable, raising=False)
        apply_patches()
        assert getattr(FakeTable, "_behave_data_patched", False) is True
        revert_patches()
        assert not hasattr(FakeTable, "_behave_data_patched")

    def test_revert_without_apply_no_error(self) -> None:
        revert_patches()
        revert_patches()


class TestNoBehaveInstalled:
    def test_apply_patches_without_behave(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import builtins

        original_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "behave.model":
                raise ImportError("No module named 'behave.model'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        apply_patches()
        revert_patches()
