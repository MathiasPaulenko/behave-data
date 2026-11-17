"""Builder registry with derived fields, nesting, and count support."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

from behave_data.errors import BehaveDataError, BuilderNotFoundError

logger = logging.getLogger(__name__)

_GLOBAL_BUILDERS: dict[str, Callable[..., dict[str, Any]]] = {}


class BuilderRegistry:
    """Registry for builders with derived fields and nesting.

    Lookups check instance registrations first, then the global registry
    populated by ``@data_builder`` — so builders registered after this
    registry was created are still visible.
    """

    def __init__(self) -> None:
        """Initialize the registry with globally registered builders."""
        self._builders: dict[str, Callable[..., dict[str, Any]]] = dict(_GLOBAL_BUILDERS)

    def _lookup(self, name: str) -> Callable[..., dict[str, Any]] | None:
        """Find a builder: instance registrations first, then globals."""
        func = self._builders.get(name)
        if func is None:
            func = _GLOBAL_BUILDERS.get(name)
        return func

    def register(self, name: str, func: Callable[..., dict[str, Any]]) -> None:
        """Register a builder function.

        Args:
            name: The builder name.
            func: A callable that accepts an overrides dict and returns a dict.

        Raises:
            TypeError: If ``name`` is not a string or ``func`` is not callable.
            ValueError: If ``name`` is empty.
        """
        if not isinstance(name, str):
            raise TypeError(f"Builder name must be a string, got {type(name).__name__}")
        if not name:
            raise ValueError("Builder name cannot be empty")
        if not callable(func):
            raise TypeError(f"Builder func must be callable, got {type(func).__name__}")
        self._builders[name] = func

    def build(
        self,
        name: str,
        count: int = 1,
        includes: dict[str, str] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Build data using the named builder.

        Args:
            name: The builder name.
            count: Number of instances to build. Returns a single dict for 1,
                a list for > 1, and an empty list for 0.
            includes: Optional mapping of field names to other builder names.
                The referenced builders are merged into the result.
            overrides: Dict merged over the builder's default values.

        Returns:
            The built dict, or a list of dicts when count > 1.

        Raises:
            BuilderNotFoundError: If the builder is not registered.
            ValueError: If count is negative.
            BehaveDataError: If a circular builder reference is detected.
        """
        if self._lookup(name) is None:
            raise BuilderNotFoundError(name)
        if count < 0:
            raise ValueError(f"count must be non-negative, got {count}")
        if includes is not None and not isinstance(includes, Mapping):
            raise TypeError(f"includes must be a dict, got {type(includes).__name__}")
        if overrides is not None and not isinstance(overrides, Mapping):
            raise TypeError(f"overrides must be a dict, got {type(overrides).__name__}")
        ov = dict(overrides) if overrides else {}
        if count == 0:
            return []
        inc = dict(includes) if includes else None
        if count == 1:
            return self._build_one(name, inc, ov)
        return [self._build_one(name, inc, ov) for _ in range(count)]

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
        func = self._lookup(name)
        if func is None:
            raise BuilderNotFoundError(name)
        data = func(dict(overrides))
        if not isinstance(data, dict):
            raise BehaveDataError(f"Builder '{name}' must return a dict, got {type(data).__name__}")
        if includes:
            for key, builder_name in includes.items():
                data[key] = self._build_one(builder_name, None, {}, in_progress | {name})
        return data

    def names(self) -> list[str]:
        """Return the list of registered builder names."""
        return list({**_GLOBAL_BUILDERS, **self._builders})


def data_builder(
    name: str,
) -> Callable[[Callable[..., dict[str, Any]]], Callable[..., dict[str, Any]]]:
    """Decorator to register a builder.

    Raises:
        TypeError: If ``name`` is not a string or the decorated object is not callable.
        ValueError: If ``name`` is empty.
    """
    if not isinstance(name, str):
        raise TypeError(f"Builder name must be a string, got {type(name).__name__}")
    if not name:
        raise ValueError("Builder name cannot be empty")

    def decorator(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        if not callable(func):
            raise TypeError(f"Builder func must be callable, got {type(func).__name__}")
        if name in _GLOBAL_BUILDERS:
            logger.warning("Builder %r re-registered — replacing previous definition", name)
        _GLOBAL_BUILDERS[name] = func
        return func

    return decorator
