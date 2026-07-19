"""Tests for behave_data.fixtures."""

from __future__ import annotations

import pytest

from behave_data.errors import BehaveDataError, FixtureNotFoundError
from behave_data.fixtures import FixtureRegistry, data_fixture


class TestFixtureRegistry:
    def test_register_and_get(self) -> None:
        reg = FixtureRegistry()
        reg.register("user", lambda: {"name": "Alice", "age": 30})
        data = reg.get("user")
        assert data["name"] == "Alice"

    def test_get_not_found(self) -> None:
        reg = FixtureRegistry()
        with pytest.raises(FixtureNotFoundError):
            reg.get("nonexistent")

    def test_get_with_overrides(self) -> None:
        reg = FixtureRegistry()
        reg.register("user", lambda: {"name": "Alice", "age": 30})
        data = reg.get("user", {"age": 25})
        assert data["age"] == 25
        assert data["name"] == "Alice"

    def test_names(self) -> None:
        reg = FixtureRegistry()
        reg.register("a", lambda: {})
        reg.register("b", lambda: {})
        assert set(reg.names()) == {"a", "b"}

    def test_ref_resolution(self) -> None:
        reg = FixtureRegistry()
        reg.register("base", lambda: {"x": 1})
        reg.register("child", lambda: {"y": "ref:base"})
        data = reg.get("child")
        assert data["y"] == {"x": 1}

    def test_circular_ref_detected(self) -> None:
        reg = FixtureRegistry()
        reg.register("a", lambda: {"b": "ref:b"})
        reg.register("b", lambda: {"a": "ref:a"})
        with pytest.raises(BehaveDataError, match="Circular"):
            reg.get("a")

    def test_ref_not_found(self) -> None:
        reg = FixtureRegistry()
        reg.register("a", lambda: {"b": "ref:nonexistent"})
        with pytest.raises(FixtureNotFoundError):
            reg.get("a")

    def test_ref_empty_name_raises(self) -> None:
        reg = FixtureRegistry()
        reg.register("a", lambda: {"b": "ref:"})
        with pytest.raises(ValueError, match="cannot be empty"):
            reg.get("a")


class TestDataFixtureDecorator:
    def test_basic_registration(self) -> None:
        @data_fixture("my_fixture")
        def my_fixture() -> dict[str, str]:
            return {"name": "Alice"}

        reg = FixtureRegistry()
        assert "my_fixture" in reg.names()
        assert reg.get("my_fixture")["name"] == "Alice"

    def test_parametrized_registration(self) -> None:
        @data_fixture("user", params=["alice", "bob"])
        def user(param: str) -> dict[str, str]:
            return {"name": param}

        reg = FixtureRegistry()
        assert "user:alice" in reg.names()
        assert "user:bob" in reg.names()
        assert reg.get("user:alice")["name"] == "alice"

    def test_global_registry_not_cleared(self) -> None:
        @data_fixture("shared_fixture")
        def shared_fixture() -> dict[str, str]:
            return {"name": "Alice"}

        reg1 = FixtureRegistry()
        reg2 = FixtureRegistry()
        assert "shared_fixture" in reg1.names()
        assert "shared_fixture" in reg2.names()

    def test_get_returns_non_dict_raises(self) -> None:
        reg = FixtureRegistry()
        reg.register("bad", lambda: None)  # type: ignore[arg-type, return-value]
        with pytest.raises(BehaveDataError, match="must return a dict"):
            reg.get("bad")

    def test_ref_returns_non_dict_raises(self) -> None:
        reg = FixtureRegistry()
        reg.register("base", lambda: None)  # type: ignore[arg-type, return-value]
        reg.register("child", lambda: {"x": "ref:base"})
        with pytest.raises(BehaveDataError, match="must return a dict"):
            reg.get("child")
