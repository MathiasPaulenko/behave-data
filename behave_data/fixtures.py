"""Fixture registry with scoping, nesting, and parametrization."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from behave_data.errors import BehaveDataError, FixtureNotFoundError

logger = logging.getLogger(__name__)

_GLOBAL_FIXTURES: dict[str, dict[str, Any]] = {}


class FixtureRegistry:
    """Registry for fixtures with scope, nesting, and parametrization.

    Lookups check instance registrations first, then the global registry
    populated by ``@data_fixture`` — so fixtures registered after this
    registry was created are still visible.

    Attributes:
        _fixtures: Mapping of fixture name to {"func": func, "scope": scope}.
    """

    def __init__(self) -> None:
        self._fixtures: dict[str, dict[str, Any]] = dict(_GLOBAL_FIXTURES)

    def _lookup(self, name: str) -> dict[str, Any] | None:
        """Find a fixture entry: instance registrations first, then globals."""
        entry = self._fixtures.get(name)
        if entry is None:
            entry = _GLOBAL_FIXTURES.get(name)
        return entry

    def register(
        self, name: str, func: Callable[..., dict[str, Any]], scope: str = "scenario"
    ) -> None:
        """Register a fixture.

        Args:
            name: Fixture name.
            func: Callable that returns a dict.
            scope: Fixture scope (e.g. "scenario", "feature").

        Raises:
            TypeError: If ``name`` is not a string or ``func`` is not callable.
            ValueError: If ``name`` is empty.
        """
        if not isinstance(name, str):
            raise TypeError(f"Fixture name must be a string, got {type(name).__name__}")
        if not name:
            raise ValueError("Fixture name cannot be empty")
        if not isinstance(scope, str):
            raise TypeError(f"scope must be a string, got {type(scope).__name__}")
        if not callable(func):
            raise TypeError(f"Fixture func must be callable, got {type(func).__name__}")
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
        if overrides is not None and not isinstance(overrides, Mapping):
            raise TypeError(f"overrides must be a dict, got {type(overrides).__name__}")
        entry = self._lookup(name)
        if entry is None:
            raise FixtureNotFoundError(name)
        data = entry["func"]()
        if not isinstance(data, dict):
            raise BehaveDataError(f"Fixture '{name}' must return a dict, got {type(data).__name__}")
        if overrides:
            data = {**data, **overrides}
        return self._resolve_refs(data, {name})

    def names(self) -> list[str]:
        """Return the list of registered fixture names."""
        return list({**_GLOBAL_FIXTURES, **self._fixtures})

    def _resolve_refs(
        self,
        data: dict[str, Any],
        in_progress: set[str],
        containers: frozenset[int] = frozenset(),
    ) -> dict[str, Any]:
        """Resolve ``ref:other`` values recursively.

        Args:
            data: Dict potentially containing ref: values.
            in_progress: Set of fixture names being resolved (for cycle detection).
            containers: Ids of containers on the current path (cycle guard).

        Returns:
            Dict with ref: values replaced by resolved fixture data.

        Raises:
            BehaveDataError: If circular reference detected.
        """
        resolved: dict[str, Any] = {}
        for key, value in data.items():
            resolved[key] = self._resolve_value(value, in_progress, containers)
        return resolved

    def _resolve_value(self, value: Any, in_progress: set[str], containers: frozenset[int]) -> Any:
        """Resolve a single value: ``ref:`` strings, nested dicts, and lists.

        ``containers`` tracks container ids along the current path so a
        self-referencing structure raises instead of recursing forever.
        """
        if isinstance(value, str) and value.startswith("ref:"):
            ref_name = value[4:]
            if not ref_name:
                raise ValueError("Fixture reference name cannot be empty in 'ref:' value")
            if ref_name in in_progress:
                raise BehaveDataError(f"Circular fixture reference: {ref_name}")
            ref_entry = self._lookup(ref_name)
            if ref_entry is None:
                raise FixtureNotFoundError(ref_name)
            ref_data = ref_entry["func"]()
            if not isinstance(ref_data, dict):
                raise BehaveDataError(
                    f"Fixture '{ref_name}' must return a dict, got {type(ref_data).__name__}"
                )
            return self._resolve_refs(ref_data, in_progress | {ref_name}, containers)
        if isinstance(value, dict):
            if id(value) in containers:
                raise BehaveDataError("Circular structure in fixture data")
            return {
                k: self._resolve_value(v, in_progress, containers | {id(value)})
                for k, v in value.items()
            }
        if isinstance(value, (list, tuple)):
            if id(value) in containers:
                raise BehaveDataError("Circular structure in fixture data")
            return [
                self._resolve_value(item, in_progress, containers | {id(value)}) for item in value
            ]
        return value


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

    Raises:
        TypeError: If ``name`` is not a string or ``params`` is not a sequence.
        ValueError: If ``name`` is empty.
    """
    if not isinstance(name, str):
        raise TypeError(f"Fixture name must be a string, got {type(name).__name__}")
    if not name:
        raise ValueError("Fixture name cannot be empty")
    if not isinstance(scope, str):
        raise TypeError(f"scope must be a string, got {type(scope).__name__}")
    if params is not None and (
        isinstance(params, (str, bytes)) or not isinstance(params, Iterable)
    ):
        raise TypeError(f"params must be a sequence of values, got {type(params).__name__}")

    def decorator(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        if not callable(func):
            raise TypeError(f"Fixture func must be callable, got {type(func).__name__}")
        if params is not None:
            for param in params:
                param_name = f"{name}:{param}"
                if param_name in _GLOBAL_FIXTURES:
                    logger.warning(
                        "Fixture %r re-registered — replacing previous definition",
                        param_name,
                    )

                def make_wrapper(
                    func: Callable[..., dict[str, Any]], param: Any
                ) -> Callable[..., dict[str, Any]]:
                    def wrapper() -> dict[str, Any]:
                        return func(param)

                    return wrapper

                _GLOBAL_FIXTURES[param_name] = {"func": make_wrapper(func, param), "scope": scope}
        else:
            if name in _GLOBAL_FIXTURES:
                logger.warning("Fixture %r re-registered — replacing previous definition", name)
            _GLOBAL_FIXTURES[name] = {"func": func, "scope": scope}
        return func

    return decorator
