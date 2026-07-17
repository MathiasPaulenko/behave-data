"""Tests for behave_data.examples."""

from __future__ import annotations

from typing import Any

from behave_data.config import Config
from behave_data.examples import (
    _find_load_tag,
    _replace_example_rows,
    load_examples_for_feature,
)


class FakeRow:
    def __init__(self, cells: list[str]) -> None:
        self.cells = cells

    def __getitem__(self, i: int) -> str:
        return self.cells[i]


class FakeTable:
    def __init__(self, headings: list[str], rows: list[FakeRow] | None = None) -> None:
        self.headings = headings
        self.rows = rows or []


class FakeExamples:
    def __init__(self, table: FakeTable, line: int = 0) -> None:
        self.table = table
        self.line = line


class FakeScenario:
    def __init__(
        self,
        tags: list[str] | None = None,
        examples: list[FakeExamples] | None = None,
        feature: Any = None,
    ) -> None:
        self.tags = tags or []
        self.examples = examples or []
        self.feature = feature


class FakeFeature:
    def __init__(self, tags: list[str] | None = None, scenarios: list[Any] | None = None) -> None:
        self.tags = tags or []
        self.scenarios = scenarios or []


class TestFindLoadTag:
    def test_tag_on_scenario(self) -> None:
        scenario = FakeScenario(tags=["@load_examples:csv:users.csv"])
        assert _find_load_tag(scenario) == "csv:users.csv"

    def test_tag_on_feature(self) -> None:
        feature = FakeFeature(tags=["@load_examples:json:data.json"])
        scenario = FakeScenario(feature=feature)
        assert _find_load_tag(scenario) == "json:data.json"

    def test_no_tag(self) -> None:
        scenario = FakeScenario(tags=["@smoke"])
        assert _find_load_tag(scenario) is None

    def test_tag_with_spaces(self) -> None:
        scenario = FakeScenario(tags=["@load_examples:  csv:users.csv  "])
        assert _find_load_tag(scenario) == "csv:users.csv"

    def test_scenario_tag_takes_priority(self) -> None:
        feature = FakeFeature(tags=["@load_examples:json:feature.json"])
        scenario = FakeScenario(tags=["@load_examples:csv:scenario.csv"], feature=feature)
        assert _find_load_tag(scenario) == "csv:scenario.csv"


class TestReplaceExampleRows:
    def test_replace_with_data(self) -> None:
        table = FakeTable(["old"], [FakeRow(["old"])])
        example = FakeExamples(table)
        data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
        _replace_example_rows(example, data)
        assert example.table.headings == ["name", "age"]
        assert len(example.table.rows) == 2

    def test_replace_empty_data(self) -> None:
        table = FakeTable(["old"], [FakeRow(["old"])])
        example = FakeExamples(table)
        _replace_example_rows(example, [])
        assert example.table.rows == []


class TestLoadExamplesForFeature:
    def test_loads_examples(self, tmp_path: Any) -> None:
        csv_file = tmp_path / "users.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")

        table = FakeTable(["old"], [FakeRow(["old"])])
        example = FakeExamples(table)
        scenario = FakeScenario(
            tags=[f"@load_examples:csv:{csv_file}"],
            examples=[example],
        )
        feature = FakeFeature(scenarios=[scenario])

        config = Config()
        load_examples_for_feature(feature, config)

        assert example.table.headings == ["name", "age"]
        assert len(example.table.rows) == 2

    def test_no_scenarios(self) -> None:
        feature = FakeFeature(scenarios=[])
        load_examples_for_feature(feature, Config())

    def test_no_load_tag(self) -> None:
        table = FakeTable(["old"], [FakeRow(["old"])])
        example = FakeExamples(table)
        scenario = FakeScenario(tags=["@smoke"], examples=[example])
        feature = FakeFeature(scenarios=[scenario])
        load_examples_for_feature(feature, Config())
        assert example.table.headings == ["old"]

    def test_no_examples_on_scenario(self, tmp_path: Any) -> None:
        csv_file = tmp_path / "users.csv"
        csv_file.write_text("name\nAlice\n", encoding="utf-8")
        scenario = FakeScenario(
            tags=[f"@load_examples:csv:{csv_file}"],
            examples=[],
        )
        feature = FakeFeature(scenarios=[scenario])
        load_examples_for_feature(feature, Config())
