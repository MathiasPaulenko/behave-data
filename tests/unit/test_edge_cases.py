"""Edge case tests for behave_data — covering uncovered lines and boundary conditions."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from behave_data.config import Config
from behave_data.diff import diff
from behave_data.errors import (
    BehaveDataError,
    FixtureNotFoundError,
    LoaderNotFoundError,
    TableDiffError,
    TypeConversionError,
)
from behave_data.fixtures import FixtureRegistry, data_fixture
from behave_data.hooks import (
    after_scenario_hook,
    before_feature_hook,
    before_scenario_hook,
    before_step_hook,
    setup_data,
)
from behave_data.loaders import load
from behave_data.loaders.yaml import YamlLoader
from behave_data.manager import DataManager
from behave_data.null import is_null, resolve_null
from behave_data.raw_table import RawTable
from behave_data.secrets import resolve_placeholder
from behave_data.types import convert_cell, parse_column_header, register_type

# --------------------------------------------------------------------------- #
# Hooks — cover before_feature_hook, before_scenario_hook, after_scenario_hook
# --------------------------------------------------------------------------- #


class FakeFeature:
    def __init__(self, tags: list[str] | None = None, scenarios: list[Any] | None = None) -> None:
        self.tags = tags or []
        self.scenarios = scenarios or []


class FakeScenario:
    def __init__(self, tags: list[str] | None = None, feature: Any = None) -> None:
        self.tags = tags or []
        self.feature = feature


class TestHooksEdge:
    def test_before_feature_no_data(self) -> None:
        ctx = MagicMock(spec=[])
        feature = FakeFeature()
        before_feature_hook(ctx, feature)

    def test_before_feature_with_data(self) -> None:
        ctx = MagicMock()
        ctx.data.config = Config()
        feature = FakeFeature()
        before_feature_hook(ctx, feature)

    def test_before_feature_data_no_config(self) -> None:
        ctx = MagicMock()
        ctx.data = MagicMock(spec=["fixture", "build", "resolve", "mask"])
        feature = FakeFeature()
        before_feature_hook(ctx, feature)

    def test_before_scenario_no_data(self) -> None:
        ctx = MagicMock(spec=[])
        scenario = FakeScenario()
        before_scenario_hook(ctx, scenario)

    def test_before_scenario_with_data(self) -> None:
        ctx = MagicMock()
        ctx._behave_data_loaded = {}
        ctx.data.fixture.return_value = {"x": 1}
        scenario = FakeScenario(tags=["@needs_data:foo"])
        before_scenario_hook(ctx, scenario)
        assert ctx._behave_data_loaded["foo"] == {"x": 1}

    def test_after_scenario_no_data(self) -> None:
        ctx = MagicMock(spec=[])
        scenario = FakeScenario()
        after_scenario_hook(ctx, scenario)

    def test_after_scenario_with_data_no_cleanup(self) -> None:
        ctx = MagicMock()
        del ctx._behave_data_cleanup
        scenario = FakeScenario()
        after_scenario_hook(ctx, scenario)

    def test_after_scenario_with_cleanup(self) -> None:
        ctx = MagicMock()
        ctx._behave_data_cleanup = True
        ctx._behave_data_cleanup_funcs = []
        scenario = FakeScenario()
        after_scenario_hook(ctx, scenario)
        assert ctx._behave_data_cleanup is False

    def test_before_step_no_table(self) -> None:
        ctx = MagicMock()
        step = MagicMock(spec=[])
        before_step_hook(ctx, step)

    def test_setup_data_with_config(self, tmp_path: Path) -> None:
        config = Config()
        ctx = MagicMock(spec=[])
        setup_data(ctx, config)
        assert hasattr(ctx, "data")

    def test_setup_data_default_config(self) -> None:
        ctx = MagicMock(spec=[])
        setup_data(ctx)
        assert hasattr(ctx, "data")


# --------------------------------------------------------------------------- #
# Secrets — cover ref resolution, vault/aws with mocks
# --------------------------------------------------------------------------- #


class TestSecretsEdge:
    def test_ref_resolves_dict_to_str(self) -> None:
        manager = MagicMock()
        manager.fixture.return_value = {"name": "Alice"}
        result = resolve_placeholder("ref:user", manager=manager)
        assert "Alice" in result

    def test_ref_resolves_non_dict_to_str(self) -> None:
        manager = MagicMock()
        manager.fixture.return_value = ["a", "b", "c"]
        result = resolve_placeholder("ref:items", manager=manager)
        assert "a" in result

    def test_secret_env_backend_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NONEXISTENT_SECRET", raising=False)
        config = Config(secret_backend="env")
        result = resolve_placeholder("secret:NONEXISTENT_SECRET", config)
        assert result is None

    def test_secret_vault_with_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("VAULT_ADDR", "http://vault:8200")
        monkeypatch.setenv("VAULT_TOKEN", "token123")
        mock_client = MagicMock()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "vault_secret"}}
        }
        mock_hvac = MagicMock()
        mock_hvac.Client.return_value = mock_client
        with patch.dict("sys.modules", {"hvac": mock_hvac}):
            config = Config(secret_backend="vault")
            result = resolve_placeholder("secret:mykey", config)
            assert result == "vault_secret"

    def test_secret_aws_with_mock(self) -> None:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {"SecretString": "aws_secret"}
        mock_boto3 = MagicMock()
        mock_boto3.client.return_value = mock_client
        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            config = Config(secret_backend="aws")
            result = resolve_placeholder("secret:mysecret", config)
            assert result == "aws_secret"

    def test_file_placeholder_strips_whitespace(self, tmp_path: Path) -> None:
        secret_file = tmp_path / "key.txt"
        secret_file.write_text("  secret_with_spaces  \n", encoding="utf-8")
        config = Config(secret_path=str(tmp_path))
        result = resolve_placeholder("file:key.txt", config)
        assert result == "secret_with_spaces"


# --------------------------------------------------------------------------- #
# Examples — cover _replace_example_rows fallback and _SimpleRow
# --------------------------------------------------------------------------- #


class TestExamplesEdge:
    def test_replace_example_rows_empty_data(self) -> None:
        from behave_data.examples import _replace_example_rows

        example = MagicMock()
        _replace_example_rows(example, [])
        example.table.rows.__eq__([])

    def test_replace_example_rows_with_data(self) -> None:
        from behave_data.examples import _replace_example_rows

        example = MagicMock()
        example.line = 5
        data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
        _replace_example_rows(example, data)
        assert example.table.headings == ["name", "age"]
        assert len(example.table.rows) == 2

    def test_simple_row_as_dict(self) -> None:
        from behave_data.examples import _SimpleRow

        row = _SimpleRow(["a", "b"], headers=["x", "y"])
        d = row.as_dict()
        assert d == {"x": "a", "y": "b"}

    def test_simple_row_getitem(self) -> None:
        from behave_data.examples import _SimpleRow

        row = _SimpleRow(["a", "b"], headers=["x", "y"])
        assert row[0] == "a"
        assert row[1] == "b"

    def test_simple_row_no_headers(self) -> None:
        from behave_data.examples import _SimpleRow

        row = _SimpleRow(["a", "b"])
        assert row.as_dict() == {}

    def test_load_examples_no_tags(self) -> None:
        from behave_data.examples import load_examples_for_feature

        feature = FakeFeature(scenarios=[FakeScenario()])
        config = Config()
        load_examples_for_feature(feature, config)

    def test_load_examples_with_tag_no_examples(self) -> None:
        from behave_data.examples import load_examples_for_feature

        scenario = FakeScenario(tags=["@load_examples:csv:nonexistent.csv"])
        feature = FakeFeature(scenarios=[scenario])
        config = Config()
        with pytest.raises((FileNotFoundError, LoaderNotFoundError)):
            load_examples_for_feature(feature, config)


# --------------------------------------------------------------------------- #
# RawTable — cover __hash__, __eq__, fallback row construction
# --------------------------------------------------------------------------- #


class FakeRowWithAsDict:
    def __init__(self, data: dict[str, str]) -> None:
        self._data = data

    def as_dict(self) -> dict[str, str]:
        return self._data


class FakeRowWithGetItem:
    def __init__(self, data: dict[str, str]) -> None:
        self._data = data

    def __getitem__(self, key: str) -> str:
        return self._data[key]


class FakeTable:
    def __init__(self, headings: list[str], rows: list[Any]) -> None:
        self.headings = headings
        self.rows = rows


class TestRawTableEdge:
    def test_hash_raises_type_error(self) -> None:
        table = FakeTable(["a", "b"], [FakeRowWithAsDict({"a": "1", "b": "2"})])
        rt = RawTable(table)
        with pytest.raises(TypeError, match="unhashable"):
            hash(rt)

    def test_eq_with_non_raw_table(self) -> None:
        table = FakeTable(["a"], [FakeRowWithAsDict({"a": "1"})])
        rt = RawTable(table)
        assert (rt == "not a table") is False

    def test_eq_with_equal_raw_table(self) -> None:
        table1 = FakeTable(["a"], [FakeRowWithAsDict({"a": "1"})])
        table2 = FakeTable(["a"], [FakeRowWithAsDict({"a": "1"})])
        assert RawTable(table1) == RawTable(table2)

    def test_eq_with_different_raw_table(self) -> None:
        table1 = FakeTable(["a"], [FakeRowWithAsDict({"a": "1"})])
        table2 = FakeTable(["a"], [FakeRowWithAsDict({"a": "2"})])
        assert RawTable(table1) != RawTable(table2)

    def test_fallback_row_with_getitem(self) -> None:
        table = FakeTable(["a", "b"], [FakeRowWithGetItem({"a": "1", "b": "2"})])
        rt = RawTable(table)
        assert rt.rows == [["a", "b"], ["1", "2"]]


# --------------------------------------------------------------------------- #
# YAML loader — cover success paths
# --------------------------------------------------------------------------- #


class TestYamlLoaderEdge:
    yaml = pytest.importorskip("yaml")

    def test_yaml_load_list(self, tmp_path: Path) -> None:
        f = tmp_path / "data.yaml"
        f.write_text("- name: Alice\n- name: Bob\n", encoding="utf-8")
        loader = YamlLoader()
        data = loader.load(str(f), Config())
        assert data == [{"name": "Alice"}, {"name": "Bob"}]

    def test_yaml_load_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "data.yaml"
        f.write_text("name: Alice\nage: 30\n", encoding="utf-8")
        loader = YamlLoader()
        data = loader.load(str(f), Config())
        assert data == [{"name": "Alice", "age": 30}]

    def test_yaml_load_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.yaml"
        f.write_text("", encoding="utf-8")
        loader = YamlLoader()
        data = loader.load(str(f), Config())
        assert data == []

    def test_yaml_load_invalid_type(self, tmp_path: Path) -> None:
        f = tmp_path / "data.yaml"
        f.write_text("42\n", encoding="utf-8")
        loader = YamlLoader()
        with pytest.raises(ValueError, match="must be a list or dict"):
            loader.load(str(f), Config())


# --------------------------------------------------------------------------- #
# Types — edge cases for conversion
# --------------------------------------------------------------------------- #


class TestTypesEdge:
    def test_convert_cell_invalid_int(self) -> None:
        with pytest.raises(TypeConversionError):
            convert_cell("not_a_number", int)

    def test_convert_cell_invalid_float(self) -> None:
        with pytest.raises(TypeConversionError):
            convert_cell("not_a_float", float)

    def test_convert_cell_invalid_bool(self) -> None:
        from behave_data.types import _parse_bool

        with pytest.raises(TypeConversionError):
            convert_cell("not_a_bool", _parse_bool)

    def test_convert_cell_invalid_date(self) -> None:
        from datetime import date

        with pytest.raises(TypeConversionError):
            convert_cell("not_a_date", date)

    def test_convert_cell_invalid_datetime(self) -> None:
        from datetime import datetime

        with pytest.raises(TypeConversionError):
            convert_cell("not_a_datetime", datetime)

    def test_parse_column_header_no_type(self) -> None:
        name, converter, nullable = parse_column_header("just_name")
        assert name == "just_name"
        assert converter is None
        assert nullable is False

    def test_parse_column_header_with_type(self) -> None:
        name, converter, nullable = parse_column_header("age:int")
        assert name == "age"
        assert converter is int
        assert nullable is False

    def test_parse_column_header_nullable(self) -> None:
        name, converter, nullable = parse_column_header("price:float?")
        assert name == "price"
        assert converter is float
        assert nullable is True

    def test_parse_column_header_unknown_type(self) -> None:
        name, converter, nullable = parse_column_header("url:https://x")
        assert name == "url:https://x"
        assert converter is None
        assert nullable is False

    def test_register_custom_type(self) -> None:
        register_type("upper", lambda v: v.upper())
        name, converter, nullable = parse_column_header("val:upper")
        assert converter is not None
        assert converter("hello") == "HELLO"
        # Clean up
        from behave_data.types import TYPE_CONVERTERS

        del TYPE_CONVERTERS["upper"]

    def test_convert_cell_none_converter(self) -> None:
        assert convert_cell("hello", None) == "hello"

    def test_convert_cell_with_column_name(self) -> None:
        with pytest.raises(TypeConversionError, match="age"):
            convert_cell("not_int", int, column_name="age", type_name="int")


# --------------------------------------------------------------------------- #
# Null — edge cases
# --------------------------------------------------------------------------- #


class TestNullEdge:
    def test_is_null_custom_markers(self) -> None:
        assert is_null("TBD", frozenset({"TBD"})) is True
        assert is_null("real_value", frozenset({"TBD"})) is False

    def test_resolve_null_with_custom_markers(self) -> None:
        assert resolve_null("TBD", frozenset({"TBD"})) is None
        assert resolve_null("real_value", frozenset({"TBD"})) == "real_value"

    def test_resolve_null_empty_string(self) -> None:
        assert resolve_null("") is None

    def test_resolve_null_none_input(self) -> None:
        assert resolve_null(None) is None  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Diff — edge cases
# --------------------------------------------------------------------------- #


class TestDiffEdge:
    def _make_table(self, headers: list[str], rows: list[list[str]]) -> Any:
        class _Row:
            def __init__(self, data: dict[str, str]) -> None:
                self._data = data

            def as_dict(self) -> dict[str, str]:
                return self._data

        class _Table:
            def __init__(self) -> None:
                self.headings = headers
                self.rows = [_Row(dict(zip(headers, cells, strict=False))) for cells in rows]

        return _Table()

    def test_diff_identical_tables(self) -> None:
        table = self._make_table(["a", "b"], [["1", "2"]])
        # diff raises on mismatch, so no exception = identical
        diff(table, [{"a": "1", "b": "2"}])

    def test_diff_empty_tables(self) -> None:
        table = self._make_table(["a"], [])
        diff(table, [])

    def test_diff_extra_rows_in_actual(self) -> None:
        table = self._make_table(["a"], [["1"]])
        with pytest.raises(TableDiffError):
            diff(table, [{"a": "1"}, {"a": "2"}])

    def test_diff_extra_rows_in_expected(self) -> None:
        table = self._make_table(["a"], [["1"], ["2"]])
        with pytest.raises(TableDiffError):
            diff(table, [{"a": "1"}])

    def test_diff_column_mismatch(self) -> None:
        table = self._make_table(["a", "b"], [["1", "2"]])
        with pytest.raises(TableDiffError):
            diff(table, [{"a": "1", "c": "2"}])

    def test_diff_raises_on_mismatch(self) -> None:
        table = self._make_table(["a"], [["1"]])
        with pytest.raises(TableDiffError):
            diff(table, [{"a": "2"}])

    def test_diff_unordered_match(self) -> None:
        table = self._make_table(["a"], [["1"], ["2"]])
        diff(table, [{"a": "2"}, {"a": "1"}], ordered=False)

    def test_diff_ignore_columns(self) -> None:
        table = self._make_table(["a", "b"], [["1", "2"]])
        diff(table, [{"a": "1", "b": "different"}], ignore_columns=["b"])


# --------------------------------------------------------------------------- #
# Fixtures — circular ref and deep nesting
# --------------------------------------------------------------------------- #


class TestFixturesEdge:
    def test_deep_nested_refs(self) -> None:
        reg = FixtureRegistry()
        reg.register("a", lambda: {"b": "ref:b"})
        reg.register("b", lambda: {"c": "ref:c"})
        reg.register("c", lambda: {"val": 42})
        data = reg.get("a")
        assert data["b"]["c"]["val"] == 42

    def test_self_ref_is_circular(self) -> None:
        reg = FixtureRegistry()
        reg.register("self_ref", lambda: {"x": "ref:self_ref"})
        with pytest.raises(BehaveDataError, match="Circular"):
            reg.get("self_ref")

    def test_ref_to_nonexistent_fixture(self) -> None:
        reg = FixtureRegistry()
        reg.register("a", lambda: {"b": "ref:nonexistent"})
        with pytest.raises(FixtureNotFoundError):
            reg.get("a")

    def test_parametrized_fixture_with_special_chars(self) -> None:
        @data_fixture("user", params=["user-1", "user-2"])
        def user(param: str) -> dict[str, str]:
            return {"name": param}

        reg = FixtureRegistry()
        assert "user:user-1" in reg.names()
        assert reg.get("user:user-1")["name"] == "user-1"


# --------------------------------------------------------------------------- #
# Loaders — edge cases
# --------------------------------------------------------------------------- #


class TestLoadersEdge:
    def test_load_unknown_schema(self) -> None:
        with pytest.raises(LoaderNotFoundError):
            load("unknown_schema:data")

    def test_load_csv_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.csv"
        f.write_text("", encoding="utf-8")
        data = load(str(f))
        assert data == []

    def test_load_json_empty_list(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.json"
        f.write_text("[]", encoding="utf-8")
        data = load(str(f))
        assert data == []

    def test_load_json_single_object(self, tmp_path: Path) -> None:
        f = tmp_path / "obj.json"
        f.write_text('{"name": "Alice"}', encoding="utf-8")
        data = load(str(f))
        assert data == [{"name": "Alice"}]

    def test_load_with_schema_prefix_csv(self, tmp_path: Path) -> None:
        f = tmp_path / "data.csv"
        f.write_text("name,age\nAlice,30\n", encoding="utf-8")
        data = load(f"csv:{f}")
        assert data == [{"name": "Alice", "age": "30"}]

    def test_load_detect_by_extension_json(self, tmp_path: Path) -> None:
        f = tmp_path / "data.json"
        f.write_text('[{"x": 1}]', encoding="utf-8")
        data = load(str(f))
        assert data == [{"x": 1}]


# --------------------------------------------------------------------------- #
# Config — edge cases
# --------------------------------------------------------------------------- #


class TestConfigEdge:
    def test_config_from_nonexistent_file(self) -> None:
        # from_file returns default Config if file doesn't exist
        c = Config.from_file("nonexistent_config.yml")
        assert c.secret_backend == "file"

    def test_config_default_values(self) -> None:
        c = Config()
        assert c.secret_backend == "file"
        assert c.secret_path == "secrets/"
        assert c.load_base_dir == "features/data/"

    def test_config_custom_null_markers(self) -> None:
        c = Config(null_markers=frozenset({"", "NULL", "nil"}))
        assert "NULL" in c.null_markers
        assert "nil" in c.null_markers


# --------------------------------------------------------------------------- #
# DataManager — masking edge cases
# --------------------------------------------------------------------------- #


class TestDataManagerEdge:
    def test_mask_integer_value(self) -> None:
        dm = DataManager()
        assert dm.mask(42) == 42

    def test_resolve_integer_passthrough(self) -> None:
        dm = DataManager()
        assert dm.resolve(42) == 42

    def test_resolve_list_passthrough(self) -> None:
        dm = DataManager()
        assert dm.resolve([1, 2, 3]) == [1, 2, 3]

    def test_fixture_with_overrides(self) -> None:
        dm = DataManager()
        dm.fixtures.register("user", lambda: {"name": "Alice", "age": 30})
        data = dm.fixture("user", age=25)
        assert data["age"] == 25
        assert data["name"] == "Alice"

    def test_build_with_count_and_overrides(self) -> None:
        dm = DataManager()
        dm.builders.register("item", lambda o: {"name": "default", **o})
        items = dm.build("item", count=2, overrides={"name": "custom"})
        assert isinstance(items, list)
        assert len(items) == 2
        assert all(i["name"] == "custom" for i in items)


# --------------------------------------------------------------------------- #
# Regression tests — Round 2
# --------------------------------------------------------------------------- #


class TestSimpleRowHeaders:
    """Regression: _SimpleRow must receive headers so as_dict() works."""

    def test_simple_row_as_dict_with_headers(self) -> None:
        from behave_data.examples import _SimpleRow

        row = _SimpleRow(["Alice", "30"], ["name", "age"])
        assert row.as_dict() == {"name": "Alice", "age": "30"}

    def test_simple_row_as_dict_empty_headers(self) -> None:
        from behave_data.examples import _SimpleRow

        row = _SimpleRow(["Alice"], [])
        assert row.as_dict() == {}


class TestSecretEmptyName:
    """Regression: secret: with empty name must raise ValueError."""

    def test_secret_empty_name_raises(self) -> None:
        from behave_data.secrets import resolve_placeholder

        with pytest.raises(ValueError, match="cannot be empty"):
            resolve_placeholder("secret:")


class TestMaskUnhashable:
    """Regression: mask() must not crash on unhashable values."""

    def test_mask_list_returns_original(self) -> None:
        dm = DataManager()
        assert dm.mask([1, 2, 3]) == [1, 2, 3]

    def test_mask_dict_returns_original(self) -> None:
        dm = DataManager()
        assert dm.mask({"key": "val"}) == {"key": "val"}


class TestJsonLoaderNonDictItems:
    """Regression: JSON list with non-dict items must raise ValueError."""

    def test_json_list_with_integers_raises(self, tmp_path: Path) -> None:
        import json as json_mod

        from behave_data.loaders.json import JsonLoader

        f = tmp_path / "data.json"
        f.write_text(json_mod.dumps([1, 2, 3]), encoding="utf-8")
        with pytest.raises(ValueError, match="must be dicts"):
            JsonLoader().load(str(f), Config())

    def test_json_list_with_strings_raises(self, tmp_path: Path) -> None:
        import json as json_mod

        from behave_data.loaders.json import JsonLoader

        f = tmp_path / "data.json"
        f.write_text(json_mod.dumps(["a", "b"]), encoding="utf-8")
        with pytest.raises(ValueError, match="must be dicts"):
            JsonLoader().load(str(f), Config())
