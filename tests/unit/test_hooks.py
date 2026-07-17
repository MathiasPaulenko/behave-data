"""Tests for behave_data.hooks."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from behave_data.config import Config
from behave_data.hooks import before_step_hook, setup_data
from behave_data.manager import DataManager


class FakeRow:
    def __init__(self, data: dict[str, str]) -> None:
        self._data = data

    def as_dict(self) -> dict[str, str]:
        return dict(self._data)

    def __getitem__(self, key: str) -> str:
        return self._data[key]


class FakeTable:
    def __init__(self, headings: list[str], rows: list[list[str]]) -> None:
        self.headings = headings
        self.rows = [FakeRow(dict(zip(headings, r, strict=False))) for r in rows]


class FakeStep:
    def __init__(self, table: Any = None) -> None:
        self.table = table


class FakeContext:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestSetupData:
    def test_creates_context_data_as_manager(self) -> None:
        ctx = FakeContext()
        config = Config()
        setup_data(ctx, config)
        assert isinstance(ctx.data, DataManager)
        assert ctx.data.config is config

    def test_applies_patches(self) -> None:
        ctx = FakeContext()
        with patch("behave_data.hooks.apply_patches") as mock_apply:
            setup_data(ctx, Config())
            mock_apply.assert_called_once()

    def test_custom_config_used(self) -> None:
        ctx = FakeContext()
        config = Config(null_markers=frozenset({"NULL"}))
        setup_data(ctx, config)
        assert ctx.data.config is config

    def test_without_config_calls_from_file(self) -> None:
        ctx = FakeContext()
        with patch.object(Config, "from_file", return_value=Config()) as mock_from_file:
            setup_data(ctx)
            mock_from_file.assert_called_once_with("behave_data.yml")
            assert isinstance(ctx.data, DataManager)


class TestBeforeStepHook:
    def test_resolves_placeholders_in_cells(self) -> None:
        ctx = FakeContext(user="Alice")
        table = FakeTable(["name"], [["{user}"]])
        step = FakeStep(table=table)
        before_step_hook(ctx, step)
        assert ctx.resolved_table["headings"] == ["name"]
        assert ctx.resolved_table["rows"] == [["name"], ["Alice"]]

    def test_without_table_no_error(self) -> None:
        ctx = FakeContext()
        step = FakeStep(table=None)
        before_step_hook(ctx, step)
        assert not hasattr(ctx, "resolved_table")

    def test_does_not_mutate_original_table(self) -> None:
        ctx = FakeContext(user="Alice")
        table = FakeTable(["name"], [["{user}"]])
        step = FakeStep(table=table)
        before_step_hook(ctx, step)
        assert table.rows[0].as_dict()["name"] == "{user}"

    def test_no_placeholders_table_unchanged_but_copied(self) -> None:
        ctx = FakeContext()
        table = FakeTable(["name", "age"], [["Alice", "30"]])
        step = FakeStep(table=table)
        before_step_hook(ctx, step)
        assert ctx.resolved_table["rows"] == [["name", "age"], ["Alice", "30"]]

    def test_multiple_placeholders_in_one_cell(self) -> None:
        ctx = FakeContext(first="John", last="Doe")
        table = FakeTable(["full"], [["{first} {last}"]])
        step = FakeStep(table=table)
        before_step_hook(ctx, step)
        assert ctx.resolved_table["rows"][1] == ["John Doe"]

    def test_nested_attribute_access(self) -> None:
        ctx = FakeContext(user=FakeContext(name="Bob"))
        table = FakeTable(["name"], [["{user.name}"]])
        step = FakeStep(table=table)
        before_step_hook(ctx, step)
        assert ctx.resolved_table["rows"][1] == ["Bob"]

    def test_unresolved_placeholder_left_unchanged(self) -> None:
        ctx = FakeContext()
        table = FakeTable(["name"], [["{unknown}"]])
        step = FakeStep(table=table)
        before_step_hook(ctx, step)
        assert ctx.resolved_table["rows"][1] == ["{unknown}"]

    def test_empty_table(self) -> None:
        ctx = FakeContext()
        table = FakeTable(["name"], [])
        step = FakeStep(table=table)
        before_step_hook(ctx, step)
        assert ctx.resolved_table["headings"] == ["name"]
        assert ctx.resolved_table["rows"] == [["name"]]
