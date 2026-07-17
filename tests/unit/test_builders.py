"""Tests for behave_data.builders."""

from __future__ import annotations

import pytest

from behave_data.builders import BuilderRegistry, data_builder
from behave_data.errors import BuilderNotFoundError


class TestBuilderRegistry:
    def test_register_and_build_single(self) -> None:
        reg = BuilderRegistry()
        reg.register("user", lambda overrides: {"name": "Alice", **overrides})
        data = reg.build("user")
        assert data["name"] == "Alice"

    def test_build_with_overrides(self) -> None:
        reg = BuilderRegistry()
        reg.register("user", lambda overrides: {"name": "Alice", **overrides})
        data = reg.build("user", overrides={"name": "Bob"})
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
        assert data["addr"] == {"city": "NYC"}


class TestDataBuilderDecorator:
    def test_basic_registration(self) -> None:
        @data_builder("my_builder")
        def my_builder(overrides: dict) -> dict:
            return {"name": "Alice", **overrides}

        reg = BuilderRegistry()
        assert "my_builder" in reg.names()
        assert reg.build("my_builder")["name"] == "Alice"
