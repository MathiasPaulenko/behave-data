"""Tests for behave_data.builders."""

from __future__ import annotations

from typing import Any

import pytest

from behave_data.builders import BuilderRegistry, data_builder
from behave_data.errors import BuilderNotFoundError


class TestBuilderRegistry:
    def test_register_and_build_single(self) -> None:
        reg = BuilderRegistry()
        reg.register("user", lambda overrides: {"name": "Alice", **overrides})
        data = reg.build("user")
        assert isinstance(data, dict)
        assert data["name"] == "Alice"

    def test_build_with_overrides(self) -> None:
        reg = BuilderRegistry()
        reg.register("user", lambda overrides: {"name": "Alice", **overrides})
        data = reg.build("user", overrides={"name": "Bob"})
        assert isinstance(data, dict)
        assert data["name"] == "Bob"

    def test_build_count(self) -> None:
        reg = BuilderRegistry()
        reg.register("user", lambda overrides: {"name": "Alice", **overrides})
        data = reg.build("user", count=3)
        assert isinstance(data, list)
        assert len(data) == 3

    def test_build_count_zero(self) -> None:
        reg = BuilderRegistry()
        reg.register("user", lambda overrides: {"name": "Alice"})
        data = reg.build("user", count=0)
        assert data == []

    def test_build_not_found(self) -> None:
        reg = BuilderRegistry()
        with pytest.raises(BuilderNotFoundError):
            reg.build("nonexistent")

    def test_build_negative_count_raises(self) -> None:
        reg = BuilderRegistry()
        reg.register("user", lambda o: {"name": "Alice"})
        with pytest.raises(ValueError, match="non-negative"):
            reg.build("user", count=-1)

    def test_circular_includes_raises(self) -> None:
        from behave_data.errors import BehaveDataError

        reg = BuilderRegistry()
        reg.register("a", lambda o: {"name": "A"})
        reg.register("b", lambda o: {"name": "B"})
        with pytest.raises(BehaveDataError, match="Circular"):
            reg.build("a", includes={"b": "b", "a": "a"})

    def test_names(self) -> None:
        reg = BuilderRegistry()
        reg.register("a", lambda o: {})
        reg.register("b", lambda o: {})
        assert set(reg.names()) == {"a", "b"}

    def test_includes(self) -> None:
        reg = BuilderRegistry()
        reg.register("address", lambda o: {"city": "NYC"})
        reg.register("user", lambda o: {"name": "Alice", **o})
        data = reg.build("user", includes={"addr": "address"})
        assert isinstance(data, dict)
        assert data["addr"] == {"city": "NYC"}

    def test_includes_missing_builder_raises(self) -> None:
        reg = BuilderRegistry()
        reg.register("user", lambda o: {"name": "Alice"})
        with pytest.raises(BuilderNotFoundError, match="nonexistent"):
            reg.build("user", includes={"addr": "nonexistent"})

    def test_build_count_does_not_mutate_overrides(self) -> None:
        reg = BuilderRegistry()

        def mutating_builder(overrides: dict[str, Any]) -> dict[str, Any]:
            overrides["mutated"] = True
            return {"name": "Alice", **overrides}

        reg.register("user", mutating_builder)
        original: dict[str, Any] = {"base": "x"}
        data = reg.build("user", count=2, overrides=original)
        assert isinstance(data, list)
        assert len(data) == 2
        assert original == {"base": "x"}
        assert data[1] == {"name": "Alice", "base": "x", "mutated": True}


class TestDataBuilderDecorator:
    def test_basic_registration(self) -> None:
        @data_builder("my_builder")
        def my_builder(overrides: dict[str, Any]) -> dict[str, Any]:
            return {"name": "Alice", **overrides}

        reg = BuilderRegistry()
        assert "my_builder" in reg.names()
        data = reg.build("my_builder")
        assert isinstance(data, dict)
        assert data["name"] == "Alice"

    def test_global_registry_not_cleared(self) -> None:
        @data_builder("shared_builder")
        def shared_builder(overrides: dict[str, Any]) -> dict[str, Any]:
            return {"name": "Alice", **overrides}

        reg1 = BuilderRegistry()
        reg2 = BuilderRegistry()
        assert "shared_builder" in reg1.names()
        assert "shared_builder" in reg2.names()

    def test_build_returns_non_dict_raises(self) -> None:
        from behave_data.errors import BehaveDataError

        reg = BuilderRegistry()
        reg.register("bad", lambda o: None)  # type: ignore[arg-type, return-value]
        with pytest.raises(BehaveDataError, match="must return a dict"):
            reg.build("bad")
