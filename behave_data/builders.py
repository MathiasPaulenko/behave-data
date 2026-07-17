"""Builder registry with derived fields, nesting, and count support."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from behave_data.errors import BehaveDataError, BuilderNotFoundError

_GLOBAL_BUILDERS: dict[str, Callable[..., dict[str, Any]]] = {}


class BuilderRegistry:
    """Registry for builders with derived fields and nesting."""

    def __init__(self) -> None:
        self._builders: dict[str, Callable[..., dict[str, Any]]] = dict(_GLOBAL_BUILDERS)
        _GLOBAL_BUILDERS.clear()

    def register(self, name: str, func: Callable[..., dict[str, Any]]) -> None:
        self._builders[name] = func

    def build(
        self,
        name: str,
        count: int = 1,
        includes: dict[str, str] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        if name not in self._builders:
            raise BuilderNotFoundError(name)
        if count < 0:
            raise ValueError(f"count must be non-negative, got {count}")
        ov = overrides or {}
        if count == 0:
            return []
        if count == 1:
            return self._build_one(name, includes, ov)
        return [self._build_one(name, includes, ov) for _ in range(count)]

    def _build_one(
        self,
        name: str,
        includes: dict[str, str] | None,
        overrides: dict[str, Any],
        in_progress: set[str] | None = None,
    ) -> dict[str, Any]:
        if in_progress is None:
            in_progress = set()
        if name in in_progress:
            raise BehaveDataError(f"Circular builder reference: {name}")
        func = self._builders[name]
        data = func(overrides)
        if includes:
            for key, builder_name in includes.items():
                data[key] = self._build_one(builder_name, None, {}, in_progress | {name})
        return data

    def names(self) -> list[str]:
        return list(self._builders.keys())


def data_builder(
    name: str,
) -> Callable[[Callable[..., dict[str, Any]]], Callable[..., dict[str, Any]]]:
    """Decorator to register a builder."""

    def decorator(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        _GLOBAL_BUILDERS[name] = func
        return func

    return decorator
