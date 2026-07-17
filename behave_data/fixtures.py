"""Fixture registry with scoping, nesting, and parametrization."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from behave_data.errors import BehaveDataError, FixtureNotFoundError

_GLOBAL_FIXTURES: dict[str, dict[str, Any]] = {}


class FixtureRegistry:
    """Registry for fixtures with scope, nesting, and parametrization.

    Attributes:
        _fixtures: Mapping of fixture name to {"func": func, "scope": scope}.
    """

    def __init__(self) -> None:
        self._fixtures: dict[str, dict[str, Any]] = dict(_GLOBAL_FIXTURES)
        _GLOBAL_FIXTURES.clear()

    def register(
        self, name: str, func: Callable[..., dict[str, Any]], scope: str = "scenario"
    ) -> None:
        """Register a fixture.

        Args:
            name: Fixture name.
            func: Callable that returns a dict.
            scope: Fixture scope (e.g. "scenario", "feature").
        """
        self._fixtures[name] = {"func": func, "scope": scope}

    def get(self, name: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get fixture data, merging overrides.

        Resolves nested ``ref:other`` references recursively.

        Args:
            name: Fixture name.
            overrides: Optional dict to merge over fixture data.

        Returns:
            Merged fixture data dict.

        Raises:
            FixtureNotFoundError: If fixture is not registered.
            BehaveDataError: If circular reference detected.
        """
        if name not in self._fixtures:
            raise FixtureNotFoundError(name)
        data = self._fixtures[name]["func"]()
        if overrides:
            data = {**data, **overrides}
        return self._resolve_refs(data, {name})

    def names(self) -> list[str]:
        """Return list of registered fixture names."""
        return list(self._fixtures.keys())

    def _resolve_refs(self, data: dict[str, Any], in_progress: set[str]) -> dict[str, Any]:
        """Resolve ``ref:other`` values recursively.

        Args:
            data: Dict potentially containing ref: values.
            in_progress: Set of fixture names being resolved (for cycle detection).

        Returns:
            Dict with ref: values replaced by resolved fixture data.

        Raises:
            BehaveDataError: If circular reference detected.
        """
        resolved: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("ref:"):
                ref_name = value[4:]
                if not ref_name:
                    raise ValueError("Fixture reference name cannot be empty in 'ref:' value")
                if ref_name in in_progress:
                    raise BehaveDataError(f"Circular fixture reference: {ref_name}")
                if ref_name not in self._fixtures:
                    raise FixtureNotFoundError(ref_name)
                ref_data = self._fixtures[ref_name]["func"]()
                ref_data = self._resolve_refs(ref_data, in_progress | {ref_name})
                resolved[key] = ref_data
            else:
                resolved[key] = value
        return resolved


def data_fixture(
    name: str,
    scope: str = "scenario",
    params: list[Any] | None = None,
) -> Callable[[Callable[..., dict[str, Any]]], Callable[..., dict[str, Any]]]:
    """Decorator to register a fixture.

    If params is provided, registers {name}:{param} per param.
    The decorated function receives param as its first argument.

    If params is None, registers name with no args.

    Args:
        name: Fixture name.
        scope: Fixture scope.
        params: Optional list of params for parametrized fixtures.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        if params is not None:
            for param in params:
                param_name = f"{name}:{param}"

                def make_wrapper(
                    func: Callable[..., dict[str, Any]], param: Any
                ) -> Callable[..., dict[str, Any]]:
                    def wrapper() -> dict[str, Any]:
                        return func(param)

                    return wrapper

                _GLOBAL_FIXTURES[param_name] = {"func": make_wrapper(func, param), "scope": scope}
        else:
            _GLOBAL_FIXTURES[name] = {"func": func, "scope": scope}
        return func

    return decorator
