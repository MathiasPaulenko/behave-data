"""Tests for behave_data.tags."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from behave_data.errors import BehaveDataError
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

    def test_needs_data_empty_name_raises(self) -> None:
        """Regression: needs_data: with empty name must raise ValueError."""
        ctx = MagicMock()
        ctx.data.fixture.return_value = {}
        ctx._behave_data_loaded = {}
        scenario = FakeScenario(tags=["@needs_data:"])
        with pytest.raises(ValueError, match="needs_data tag requires a fixture name"):
            process_tags_before_scenario(ctx, scenario)

    def test_with_fixture_empty_name_raises(self) -> None:
        """Regression: with_fixture: with empty name must raise ValueError."""
        ctx = MagicMock()
        ctx.data.fixture.return_value = {}
        scenario = FakeScenario(tags=["@with_fixture:"])
        with pytest.raises(ValueError, match="with_fixture tag requires a fixture name"):
            process_tags_before_scenario(ctx, scenario)

    def test_needs_data_whitespace_name_raises(self) -> None:
        """Regression: needs_data: with whitespace-only name must raise ValueError."""
        ctx = MagicMock()
        ctx.data.fixture.return_value = {}
        ctx._behave_data_loaded = {}
        scenario = FakeScenario(tags=["@needs_data:   "])
        with pytest.raises(ValueError, match="needs_data tag requires a fixture name"):
            process_tags_before_scenario(ctx, scenario)

    def test_with_fixture_whitespace_name_raises(self) -> None:
        """Regression: with_fixture: with whitespace-only name must raise ValueError."""
        ctx = MagicMock()
        ctx.data.fixture.return_value = {}
        scenario = FakeScenario(tags=["@with_fixture:   "])
        with pytest.raises(ValueError, match="with_fixture tag requires a fixture name"):
            process_tags_before_scenario(ctx, scenario)

    def test_needs_data_strips_whitespace_from_name(self) -> None:
        """Regression: needs_data: name should be stripped of whitespace."""
        ctx = MagicMock()
        ctx.data.fixture.return_value = {"name": "Alice"}
        ctx._behave_data_loaded = {}
        scenario = FakeScenario(tags=["@needs_data:  user  "])
        process_tags_before_scenario(ctx, scenario)
        ctx.data.fixture.assert_called_once_with("user")
        assert ctx._behave_data_loaded["user"] == {"name": "Alice"}


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

    def test_cleanup_executes_no_arg_funcs(self) -> None:
        ctx = MagicMock()
        ctx._behave_data_cleanup = True
        called: list[bool] = []
        ctx._behave_data_cleanup_funcs = [lambda: called.append(True)]
        scenario = FakeScenario()
        process_tags_after_scenario(ctx, scenario)
        assert called == [True]
        assert ctx._behave_data_cleanup is False

    def test_cleanup_executes_mixed_funcs(self) -> None:
        ctx = MagicMock()
        ctx._behave_data_cleanup = True
        results: list[str] = []
        ctx._behave_data_cleanup_funcs = [
            lambda c: results.append("with_ctx"),
            lambda: results.append("no_ctx"),
        ]
        scenario = FakeScenario()
        process_tags_after_scenario(ctx, scenario)
        assert results == ["with_ctx", "no_ctx"]
        assert ctx._behave_data_cleanup is False

    def test_cleanup_funcs_list_cleared_after_run(self) -> None:
        ctx = MagicMock()
        ctx._behave_data_cleanup = True
        ctx._behave_data_cleanup_funcs = [lambda: None]
        scenario = FakeScenario()
        process_tags_after_scenario(ctx, scenario)
        assert ctx._behave_data_cleanup_funcs == []

    def test_cleanup_funcs_cleared_even_when_one_raises(self) -> None:
        ctx = MagicMock()
        ctx._behave_data_cleanup = True

        def bad_cleanup() -> None:
            raise RuntimeError("boom")

        ctx._behave_data_cleanup_funcs = [bad_cleanup]
        scenario = FakeScenario()
        with pytest.raises(RuntimeError, match="boom"):
            process_tags_after_scenario(ctx, scenario)
        assert ctx._behave_data_cleanup is False
        assert ctx._behave_data_cleanup_funcs == []

    def test_non_callable_cleanup_raises_behave_data_error(self) -> None:
        ctx = MagicMock()
        ctx._behave_data_cleanup = True
        ctx._behave_data_cleanup_funcs = ["not_callable"]
        scenario = FakeScenario()
        with pytest.raises(BehaveDataError, match="must be callable"):
            process_tags_after_scenario(ctx, scenario)
        assert ctx._behave_data_cleanup_funcs == []

    def test_stale_cleanup_state_reset_before_scenario(self) -> None:
        """Regression: leftover cleanup flag from a skipped after_scenario must not leak."""
        ctx = MagicMock()
        ctx._behave_data_cleanup = True
        ctx._behave_data_cleanup_funcs = [lambda: ctx.record.append("stale")]
        scenario = FakeScenario()
        process_tags_before_scenario(ctx, scenario)
        assert ctx._behave_data_cleanup is False
        assert ctx._behave_data_cleanup_funcs == []

    def test_cleanup_func_with_uninspectable_signature_called_without_context(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def broken_signature(func: object) -> object:
            raise ValueError("no signature")

        monkeypatch.setattr("behave_data.tags.inspect.signature", broken_signature)

        ctx = MagicMock()
        ctx._behave_data_cleanup = True
        called: list[bool] = []
        ctx._behave_data_cleanup_funcs = [lambda: called.append(True)]
        scenario = FakeScenario()
        process_tags_after_scenario(ctx, scenario)
        assert called == [True]

    def test_cleanup_continues_after_error(self) -> None:
        """Regression: one cleanup failure should not stop subsequent cleanups."""
        ctx = MagicMock()
        ctx._behave_data_cleanup = True
        results: list[str] = []

        def good1() -> None:
            results.append("good1")

        def bad() -> None:
            raise RuntimeError("boom")

        def good2() -> None:
            results.append("good2")

        ctx._behave_data_cleanup_funcs = [good1, bad, good2]
        scenario = FakeScenario()
        with pytest.raises(RuntimeError, match="boom"):
            process_tags_after_scenario(ctx, scenario)
        assert results == ["good1", "good2"]
        assert ctx._behave_data_cleanup is False
        assert ctx._behave_data_cleanup_funcs == []
