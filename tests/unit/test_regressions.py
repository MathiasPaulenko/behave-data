"""Regression tests for bugs found during the production audit."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from behave_data import (
    Config,
    DataManager,
    data_builder,
    data_fixture,
    diff,
    raw_table,
    register_type,
    typed_wrap,
    wrap,
)
from behave_data.builders import BuilderRegistry
from behave_data.errors import BehaveDataError
from behave_data.examples import _find_load_tag, _replace_example_rows
from behave_data.fixtures import FixtureRegistry
from behave_data.loaders import load
from behave_data.secrets import resolve_placeholder
from behave_data.tags import _safe_attr_name, process_tags_before_scenario
from behave_data.types import convert_cell


class TestDiffTableWrapper:
    """diff() must accept behave-tables TableWrapper objects, not only raw tables."""

    def test_plain_table_wrapper(self, make_table: Any) -> None:
        table = make_table(["a"], [["1"]])
        wrapped = wrap(table)
        diff(wrapped, [{"a": "1"}])

    def test_table_wrapper_mismatch_raises(self, make_table: Any) -> None:
        from behave_data.errors import TableDiffError

        table = make_table(["a"], [["1"]])
        with pytest.raises(TableDiffError):
            diff(wrap(table), [{"a": "2"}])

    def test_typed_wrapper_as_expected(self, make_table: Any) -> None:
        table = make_table(["a"], [["1"]])
        diff(typed_wrap(table), [{"a": "1"}])


class TestDiffIgnoreColumns:
    def test_single_string_is_one_column(self, make_table: Any) -> None:
        table = make_table(["ab", "c"], [["1", "2"]])
        # "ab" must be treated as the column name, not split into {"a", "b"} —
        # column "ab" is ignored, so differing values there must not raise.
        diff(table, [{"ab": "9", "c": "2"}], ignore_columns="ab")

    def test_list_still_works(self, make_table: Any) -> None:
        table = make_table(["ab", "c"], [["1", "2"]])
        diff(table, [{"ab": "9", "c": "2"}], ignore_columns=["ab"])

    def test_non_iterable_raises(self, make_table: Any) -> None:
        table = make_table(["a"], [["1"]])
        with pytest.raises(TypeError):
            diff(table, [{"a": "1"}], ignore_columns=42)


class TestConfigValidation:
    def test_from_dict_non_mapping(self) -> None:
        with pytest.raises(TypeError):
            Config.from_dict("null_markers")  # type: ignore[arg-type]

    def test_from_dict_non_string_keys(self) -> None:
        with pytest.raises(TypeError):
            Config.from_dict({1: "x"})

    def test_null_markers_by_column_non_string_key(self) -> None:
        with pytest.raises(TypeError):
            Config(null_markers_by_column={123: frozenset({"x"})})  # type: ignore[dict-item]

    def test_type_overrides_non_string_key(self) -> None:
        with pytest.raises(TypeError):
            Config(type_overrides={123: "int"})  # type: ignore[dict-item]

    def test_db_connections_non_string_key(self) -> None:
        with pytest.raises(TypeError):
            Config(db_connections={123: "sqlite:///"})  # type: ignore[dict-item]

    def test_data_sources_non_string_key(self) -> None:
        with pytest.raises(TypeError):
            Config(data_sources={123: "csv:x.csv"})  # type: ignore[dict-item]

    def test_unknown_secret_backend_fails_fast(self) -> None:
        with pytest.raises(ValueError, match="secret_backend"):
            Config(secret_backend="bogus")

    def test_from_file_directory(self, tmp_path: Path) -> None:
        with pytest.raises(BehaveDataError, match="not a file"):
            Config.from_file(str(tmp_path))


class TestTypedTableValidation:
    def test_typed_wrap_non_table(self) -> None:
        with pytest.raises(TypeError):
            typed_wrap(object())  # type: ignore[arg-type]

    def test_typed_wrap_bad_config(self, make_table: Any) -> None:
        table = make_table(["a"], [["1"]])
        with pytest.raises(TypeError):
            typed_wrap(table, "not a config")  # type: ignore[arg-type]

    def test_typed_dicts_bad_config(self, make_table: Any) -> None:
        wrapper = typed_wrap(make_table(["a"], [["1"]]))
        with pytest.raises(TypeError):
            wrapper.typed_dicts("not a config")  # type: ignore[arg-type]

    def test_duplicate_clean_names_raise(self, make_table: Any) -> None:
        table = make_table(["x:int", "x:float"], [["1", "2"]])
        with pytest.raises(ValueError, match="Duplicate column"):
            typed_wrap(table).typed_dicts()

    def test_duplicate_identical_headers_raise(self, make_table: Any) -> None:
        table = make_table(["x", "x"], [["1", "2"]])
        with pytest.raises(ValueError, match="Duplicate column"):
            typed_wrap(table).typed_dicts()

    def test_distinct_clean_names_ok(self, make_table: Any) -> None:
        table = make_table(["x:int", "y:float"], [["1", "2"]])
        assert typed_wrap(table).typed_dicts() == [{"x": 1, "y": 2.0}]


class TestRawTableValidation:
    def test_raw_table_non_table(self) -> None:
        with pytest.raises(TypeError):
            raw_table(object())

    def test_raw_table_table_wrapper(self, make_table: Any) -> None:
        table = make_table(["a"], [["1"]])
        raw = raw_table(table)
        assert raw[0] == ["a"]


class TestLoadSourceTypes:
    def test_path_object(self, tmp_path: Path) -> None:
        csv = tmp_path / "data.csv"
        csv.write_text("a,b\n1,2\n", encoding="utf-8")
        assert load(csv) == [{"a": "1", "b": "2"}]

    def test_non_string_source(self) -> None:
        with pytest.raises(TypeError):
            load(123)  # type: ignore[arg-type]

    def test_bad_config_type(self) -> None:
        with pytest.raises(TypeError):
            load("csv:x.csv", "not a config")  # type: ignore[arg-type]

    def test_directory_source(self, tmp_path: Path) -> None:
        subdir = tmp_path / "data.csv"
        subdir.mkdir()
        with pytest.raises(FileNotFoundError):
            load(f"csv:{subdir}")


class TestSecretsValidation:
    def test_resolve_placeholder_bad_config(self) -> None:
        with pytest.raises(TypeError):
            resolve_placeholder("env:PATH", 42)  # type: ignore[arg-type]

    def test_file_placeholder_on_directory(self, tmp_path: Path) -> None:
        cfg = Config(secret_path=str(tmp_path))
        (tmp_path / "dir_secret").mkdir()
        with pytest.raises(FileNotFoundError):
            resolve_placeholder("file:dir_secret", cfg)

    def test_secret_backend_file_on_directory(self, tmp_path: Path) -> None:
        cfg = Config(secret_path=str(tmp_path))
        (tmp_path / "dir_secret").mkdir()
        with pytest.raises(FileNotFoundError):
            resolve_placeholder("secret:dir_secret", cfg)


class TestMaskOverlappingSecrets:
    def test_longer_secret_masked_not_partial(self, tmp_path: Path) -> None:
        (tmp_path / "short").write_text("xy", encoding="utf-8")
        (tmp_path / "long").write_text("xyz", encoding="utf-8")
        cfg = Config(secret_path=str(tmp_path))
        dm = DataManager(cfg)
        short = dm.resolve("secret:short")
        long = dm.resolve("secret:long")
        # "xyz" must fully mask — a partial mask would leak the trailing "z".
        assert dm.mask(long) == "***"
        assert dm.mask(f"{long}-{short}") == "***-***"

    def test_mask_is_deterministic(self, tmp_path: Path) -> None:
        (tmp_path / "a").write_text("tok", encoding="utf-8")
        (tmp_path / "b").write_text("token", encoding="utf-8")
        dm = DataManager(Config(secret_path=str(tmp_path)))
        dm.resolve("secret:a")
        dm.resolve("secret:b")
        assert dm.mask("token") == "***"


class TestNullHelpers:
    def test_get_column_markers_bad_config(self) -> None:
        from behave_data.null import get_column_markers

        with pytest.raises(TypeError):
            get_column_markers("col", 42)  # type: ignore[arg-type]


class TestNestedFixtureRefs:
    def test_ref_inside_nested_dict(self) -> None:
        reg = FixtureRegistry()
        reg.register("inner", lambda: {"v": 1})
        reg.register("outer", lambda: {"nested": {"ref_field": "ref:inner"}})
        assert reg.get("outer") == {"nested": {"ref_field": {"v": 1}}}

    def test_ref_inside_list(self) -> None:
        reg = FixtureRegistry()
        reg.register("inner", lambda: {"v": 1})
        reg.register("outer", lambda: {"items": ["ref:inner", "literal"]})
        assert reg.get("outer") == {"items": [{"v": 1}, "literal"]}

    def test_circular_ref_through_nested_dict(self) -> None:
        reg = FixtureRegistry()
        reg.register("loop", lambda: {"nested": {"x": "ref:loop"}})
        with pytest.raises(BehaveDataError, match="Circular"):
            reg.get("loop")

    def test_self_referencing_dict_raises_not_recursion_error(self) -> None:
        reg = FixtureRegistry()
        cyclic: dict[str, Any] = {"v": 1}
        cyclic["self"] = cyclic
        reg.register("loop", lambda: cyclic)
        with pytest.raises(BehaveDataError, match="Circular structure"):
            reg.get("loop")

    def test_self_referencing_list_raises(self) -> None:
        reg = FixtureRegistry()
        cyclic_list: list[Any] = [1]
        cyclic_list.append(cyclic_list)
        reg.register("loop", lambda: {"items": cyclic_list})
        with pytest.raises(BehaveDataError, match="Circular structure"):
            reg.get("loop")

    def test_shared_dict_not_circular(self) -> None:
        reg = FixtureRegistry()
        shared = {"ref_field": "ref:inner"}
        reg.register("inner", lambda: {"v": 1})
        reg.register("outer", lambda: {"a": shared, "b": shared})
        result = reg.get("outer")
        assert result["a"] == {"ref_field": {"v": 1}}
        assert result["b"] == {"ref_field": {"v": 1}}

    def test_ref_in_overrides(self) -> None:
        reg = FixtureRegistry()
        reg.register("inner", lambda: {"v": 1})
        reg.register("outer", lambda: {"a": 1})
        assert reg.get("outer", {"b": "ref:inner"}) == {"a": 1, "b": {"v": 1}}


class TestRegistryValidation:
    def test_fixture_register_validates(self) -> None:
        reg = FixtureRegistry()
        with pytest.raises(TypeError):
            reg.register(123, lambda: {})  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            reg.register("", lambda: {})
        with pytest.raises(TypeError):
            reg.register("x", "not callable")  # type: ignore[arg-type]

    def test_fixture_get_bad_overrides(self) -> None:
        reg = FixtureRegistry()
        reg.register("x", lambda: {"a": 1})
        with pytest.raises(TypeError):
            reg.get("x", "not a dict")  # type: ignore[arg-type]

    def test_builder_register_validates(self) -> None:
        reg = BuilderRegistry()
        with pytest.raises(TypeError):
            reg.register(123, lambda o: {})  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            reg.register("", lambda o: {})
        with pytest.raises(TypeError):
            reg.register("x", "not callable")  # type: ignore[arg-type]

    def test_build_bad_includes(self) -> None:
        reg = BuilderRegistry()
        reg.register("x", lambda o: {"a": 1})
        with pytest.raises(TypeError):
            reg.build("x", includes="a:b")  # type: ignore[arg-type]

    def test_build_bad_overrides(self) -> None:
        reg = BuilderRegistry()
        reg.register("x", lambda o: {"a": 1})
        with pytest.raises(TypeError):
            reg.build("x", overrides="bad")  # type: ignore[arg-type]

    def test_data_fixture_string_params_rejected(self) -> None:
        with pytest.raises(TypeError):
            data_fixture("user", params="ab")

    def test_data_fixture_non_iterable_params(self) -> None:
        with pytest.raises(TypeError):
            data_fixture("user", params=42)  # type: ignore[arg-type]

    def test_fixture_scope_non_string(self) -> None:
        reg = FixtureRegistry()
        with pytest.raises(TypeError):
            reg.register("x", lambda: {}, scope=123)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            data_fixture("x", scope=123)  # type: ignore[arg-type]

    def test_from_userdata_non_mapping(self) -> None:
        with pytest.raises(TypeError):
            Config.from_userdata("not a dict")  # type: ignore[arg-type]

    def test_data_fixture_name_validation(self) -> None:
        with pytest.raises(TypeError):
            data_fixture(123)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            data_fixture("")

    def test_data_builder_name_validation(self) -> None:
        with pytest.raises(TypeError):
            data_builder(123)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            data_builder("")


class TestSafeAttrName:
    def test_parametrized_maps_to_name_param(self) -> None:
        assert _safe_attr_name("regular_user:alice") == "regular_user_alice"

    def test_underscore_names_rejected(self) -> None:
        assert _safe_attr_name("_behave_data_loaded") is None
        assert _safe_attr_name("__class__") is None
        assert _safe_attr_name("_private") is None

    def test_reserved_rejected(self) -> None:
        assert _safe_attr_name("data") is None
        assert _safe_attr_name("config") is None

    def test_parametrized_fixture_sets_param_attr(self) -> None:
        context = SimpleNamespace(data=SimpleNamespace(fixture=lambda n: {"name": n}))
        scenario = SimpleNamespace(tags=["needs_data:regular_user:alice"], parent=None)
        process_tags_before_scenario(context, scenario)
        assert context.regular_user_alice == {"name": "regular_user:alice"}


class TestRuleAndParentTags:
    def test_needs_data_on_rule_parent(self) -> None:
        rule = SimpleNamespace(tags=["needs_data:user"], parent=None)
        scenario = SimpleNamespace(tags=[], parent=rule)
        context = SimpleNamespace(data=SimpleNamespace(fixture=lambda n: {"n": n}))
        process_tags_before_scenario(context, scenario)
        assert context.user == {"n": "user"}

    def test_rule_plus_feature_tags(self) -> None:
        feature = SimpleNamespace(tags=["needs_data:feat"], parent=None)
        rule = SimpleNamespace(tags=["needs_data:rule_data"], parent=feature)
        scenario = SimpleNamespace(tags=["needs_data:scen"], parent=rule)
        context = SimpleNamespace(data=SimpleNamespace(fixture=lambda n: {"n": n}))
        process_tags_before_scenario(context, scenario)
        assert context.scen == {"n": "scen"}
        assert context.rule_data == {"n": "rule_data"}
        assert context.feat == {"n": "feat"}

    def test_no_duplicate_feature_tags(self) -> None:
        calls: list[str] = []

        def fixture(name: str) -> dict[str, Any]:
            calls.append(name)
            return {"n": name}

        feature = SimpleNamespace(tags=["needs_data:f"], parent=None)
        # scenario.feature is the same object the parent chain reaches.
        scenario = SimpleNamespace(tags=[], parent=feature, feature=feature)
        context = SimpleNamespace(data=SimpleNamespace(fixture=fixture))
        process_tags_before_scenario(context, scenario)
        assert calls == ["f"]


class FakeTable:
    def __init__(self, headings: list[str], rows: list[Any] | None = None) -> None:
        self.headings = headings
        self.rows = rows or []
        self.modified = False


class FakeExamples:
    def __init__(self, table: Any, tags: list[str] | None = None, line: int = 10) -> None:
        self.table = table
        self.tags = tags or []
        self.line = line


class TestReplaceExampleRows:
    def test_modified_flag_set(self) -> None:
        table = FakeTable(["p"], [["x"]])
        _replace_example_rows(FakeExamples(table), [{"a": "1"}])
        assert table.modified is True

    def test_modified_flag_set_on_empty(self) -> None:
        table = FakeTable(["p"], [["x"]])
        _replace_example_rows(FakeExamples(table), [])
        assert table.modified is True
        assert table.rows == []

    def test_union_of_keys_headers(self) -> None:
        table = FakeTable(["p"], [["x"]])
        _replace_example_rows(FakeExamples(table), [{"a": "1"}, {"a": "2", "b": "3"}])
        assert table.headings == ["a", "b"]
        row_dicts = [r.as_dict() for r in table.rows]
        assert row_dicts == [{"a": "1", "b": ""}, {"a": "2", "b": "3"}]

    def test_row_lines_increase(self) -> None:
        table = FakeTable(["p"], [["x"]])
        table.line = 20
        _replace_example_rows(FakeExamples(table), [{"a": "1"}, {"a": "2"}])
        lines = [r.line for r in table.rows]
        assert lines == sorted(lines) and len(set(lines)) == 2


class TestRuleScenariosEndToEnd:
    def test_examples_load_for_rule_scenario(self, tmp_path: Path) -> None:
        """feature.scenarios is empty when scenarios live under a Rule —
        load_examples_for_feature must iterate rule.scenarios too."""
        pytest.importorskip("behave")
        from behave.parser import parse_feature

        from behave_data.examples import load_examples_for_feature

        (tmp_path / "users.csv").write_text("a\n1\n2\n3\n", encoding="utf-8")
        feature = parse_feature(
            """
Feature: f
  @load_examples:csv:users.csv
  Rule: r
    Scenario Outline: login
      Given x <a>
      Examples:
        | a |
        | 9 |
"""
        )
        rule = feature.rules[0]
        load_examples_for_feature(feature, Config(load_base_dir=str(tmp_path)))
        table = rule.scenarios[0].examples[0].table
        assert table.headings == ["a"]
        assert [list(r.cells) for r in table.rows] == [["1"], ["2"], ["3"]]
        assert table.modified is True

    def test_rule_tag_found_via_parent(self) -> None:
        pytest.importorskip("behave")
        from behave.parser import parse_feature

        feature = parse_feature(
            """
Feature: f
  @load_examples:csv:users.csv
  Rule: r
    Scenario Outline: s
      Given x <a>
      Examples:
        | a |
        | 9 |
"""
        )
        assert _find_load_tag(feature.rules[0].scenarios[0]) == "csv:users.csv"

    def test_block_tag_without_scenario_tag(self, tmp_path: Path) -> None:
        """An @load_examples tag on the Examples block alone must load —
        previously the scenario-level continue skipped it entirely."""
        pytest.importorskip("behave")
        from behave.parser import parse_feature

        from behave_data.examples import load_examples_for_feature

        (tmp_path / "only.csv").write_text("a\n4\n5\n", encoding="utf-8")
        feature = parse_feature(
            """
Feature: f
  Scenario Outline: s
    Given x <a>
    @load_examples:csv:only.csv
    Examples: block
      | a |
      | 0 |
"""
        )
        load_examples_for_feature(feature, Config(load_base_dir=str(tmp_path)))
        table = feature.scenarios[0].examples[0].table
        assert [list(r.cells) for r in table.rows] == [["4"], ["5"]]

    def test_block_tag_overrides_scenario_tag(self, tmp_path: Path) -> None:
        pytest.importorskip("behave")
        from behave.parser import parse_feature

        from behave_data.examples import load_examples_for_feature

        (tmp_path / "users.csv").write_text("a\n1\n2\n", encoding="utf-8")
        (tmp_path / "other.csv").write_text("a\n7\n8\n9\n", encoding="utf-8")
        feature = parse_feature(
            """
Feature: f
  @load_examples:csv:users.csv
  Scenario Outline: s
    Given x <a>
    @load_examples:csv:other.csv
    Examples: block
      | a |
      | 0 |
"""
        )
        load_examples_for_feature(feature, Config(load_base_dir=str(tmp_path)))
        table = feature.scenarios[0].examples[0].table
        assert [list(r.cells) for r in table.rows] == [["7"], ["8"], ["9"]]


class TestFindLoadTagParents:
    def test_tag_on_rule_parent(self) -> None:
        rule = SimpleNamespace(tags=["load_examples:csv:users.csv"], parent=None)
        scenario = SimpleNamespace(tags=[], parent=rule)
        assert _find_load_tag(scenario) == "csv:users.csv"

    def test_block_tag_ignores_feature(self) -> None:
        # An Examples block must not inherit the feature-level tag —
        # that would shadow the scenario-resolved source.
        feature = SimpleNamespace(tags=["load_examples:csv:feat.csv"])
        example = SimpleNamespace(tags=[], feature=feature)
        assert _find_load_tag(example, include_parents=False) is None

    def test_block_own_tag_wins(self) -> None:
        feature = SimpleNamespace(tags=["load_examples:csv:feat.csv"])
        example = SimpleNamespace(tags=["load_examples:csv:block.csv"], feature=feature)
        assert _find_load_tag(example, include_parents=False) == "csv:block.csv"


class TestTypeRegistration:
    def test_register_type_validates(self) -> None:
        with pytest.raises(TypeError):
            register_type(123, str)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            register_type("", str)
        with pytest.raises(TypeError):
            register_type("x", "not callable")  # type: ignore[arg-type]

    def test_convert_cell_non_callable(self) -> None:
        with pytest.raises(TypeError):
            convert_cell("1", "int")  # type: ignore[arg-type]


class TestExcelEmptyHeaders:
    def test_empty_headers_become_col_names(self, tmp_path: Path) -> None:
        openpyxl = pytest.importorskip("openpyxl")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["a", None, "c"])
        ws.append([1, 2, 3])
        path = tmp_path / "data.xlsx"
        wb.save(path)

        from behave_data.loaders.excel import ExcelLoader

        rows = ExcelLoader().load(str(path), Config())
        assert rows == [{"a": 1, "col_1": 2, "c": 3}]
