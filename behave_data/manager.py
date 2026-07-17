"""DataManager — unified access point for fixtures, builders, and secrets."""

from __future__ import annotations

from typing import Any

from behave_data.builders import BuilderRegistry
from behave_data.config import Config
from behave_data.fixtures import FixtureRegistry
from behave_data.secrets import resolve_placeholder


class DataManager:
    """Unified data manager for fixtures, builders, and secret resolution.

    Attributes:
        config: The behave-data configuration.
        fixtures: The FixtureRegistry instance.
        builders: The BuilderRegistry instance.
        _secret_hashes: Set of hash() values for masked secrets.
    """

    def __init__(self, config: Config | None = None) -> None:
        self.config = config if config is not None else Config()
        self.fixtures = FixtureRegistry()
        self.builders = BuilderRegistry()
        self._secret_hashes: set[int] = set()

    def fixture(self, name: str, **overrides: Any) -> dict[str, Any]:
        """Delegate to FixtureRegistry.get()."""
        return self.fixtures.get(name, overrides or None)

    def build(
        self,
        name: str,
        count: int = 1,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Delegate to BuilderRegistry.build()."""
        return self.builders.build(name, count=count, overrides=overrides)

    def resolve(self, value: Any) -> Any:
        """Resolve a placeholder string via secrets.resolve_placeholder().

        If value starts with ``secret:``, stores hash of result in _secret_hashes.

        Args:
            value: The value to resolve. Non-string values returned as-is.

        Returns:
            Resolved value, or original value if not a string.
        """
        if not isinstance(value, str):
            return value
        is_secret = value.startswith("secret:")
        result = resolve_placeholder(value, self.config, manager=self)
        if is_secret and result is not None:
            self._secret_hashes.add(hash(result))
        return result

    def mask(self, value: Any) -> Any:
        """Mask a value if it was resolved from a secret.

        Args:
            value: The value to check.

        Returns:
            ``"***"`` if value hash is in _secret_hashes, else original value.
            None returns None. Unhashable values return original value.
        """
        if value is None:
            return None
        try:
            if hash(value) in self._secret_hashes:
                return "***"
        except TypeError:
            pass
        return value
