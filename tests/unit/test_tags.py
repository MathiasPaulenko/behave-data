"""Tests for behave_data.tags."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from behave_data.tags import process_tags_after_scenario, process_tags_before_scenario


class FakeScenario:
    def __init__(self, tags: list[str] | None = None, feature: Any = None) -> None:
        self.tags = tags or []
        self.feature = feature


class FakeFeature:
    def __init__(self, tags: list[str] | None = None) -> None:
        self.tags = tags or []


class TestProcessTagsBeforeScenario:
    def test_no_data_attribute(self) -> None:
        ctx = MagicMock(spec=[])
        scenario = FakeScenario(tags=["@needs_data:user"])
        process_tags_before_scenario(ctx, scenario)

    def test_needs_data_tag(self) -> None:
        ctx = MagicMock()
        ctx.data.fixture.return_value = {"name": "Alice"}
        ctx._behave_data_loaded = {}
        scenario = FakeScenario(tags=["@needs_data:user"])
        process_tags_before_scenario(ctx, scenario)
        ctx.data.fixture.assert_called_once_with("user")
        assert ctx._behave_data_loaded["user"] == {"name": "Alice"}

    def test_with_fixture_tag(self) -> None:
        ctx = MagicMock()
        ctx.data.fixture.return_value = {"name": "Alice"}
        scenario = FakeScenario(tags=["@with_fixture:user"])
        process_tags_before_scenario(ctx, scenario)
        assert ctx.user == {"name": "Alice"}

    def test_cleanup_after_tag(self) -> None:
        ctx = MagicMock()
        scenario = FakeScenario(tags=["@cleanup_after"])
        process_tags_before_scenario(ctx, scenario)
        assert ctx._behave_data_cleanup is True

    def test_feature_tags_also_processed(self) -> None:
        ctx = MagicMock()
        ctx.data.fixture.return_value = {"name": "Bob"}
        feature = FakeFeature(tags=["@needs_data:from_feature"])
        scenario = FakeScenario(feature=feature)
        process_tags_before_scenario(ctx, scenario)
        ctx.data.fixture.assert_called_once_with("from_feature")


class TestProcessTagsAfterScenario:
    def test_no_cleanup_flag(self) -> None:
        ctx = MagicMock(spec=[])
        scenario = FakeScenario()
        process_tags_after_scenario(ctx, scenario)

    def test_cleanup_executes_funcs(self) -> None:
        ctx = MagicMock()
        ctx._behave_data_cleanup = True
        ctx._behave_data_cleanup_funcs = [lambda c: setattr(c, "cleaned", True)]
        scenario = FakeScenario()
        process_tags_after_scenario(ctx, scenario)
        assert ctx.cleaned is True
        assert ctx._behave_data_cleanup is False
