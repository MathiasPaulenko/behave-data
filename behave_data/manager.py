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
        _secret_values: Set of values resolved from ``secret:`` placeholders.
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the DataManager with a Config.

        Args:
            config: behave-data configuration. If None, a default Config is used.

        Raises:
            TypeError: If config is not a Config instance or None.
        """
        if config is not None and not isinstance(config, Config):
            raise TypeError(
                f"config must be a Config instance or None, got {type(config).__name__}"
            )
        self.config = config if config is not None else Config()
        self.fixtures = FixtureRegistry()
        self.builders = BuilderRegistry()
        self._secret_values: set[str] = set()

    def fixture(self, name: str, **overrides: Any) -> dict[str, Any]:
        """Delegate to FixtureRegistry.get()."""
        return self.fixtures.get(name, overrides or None)

    def build(
        self,
        name: str,
        count: int = 1,
        includes: dict[str, str] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Delegate to BuilderRegistry.build()."""
        return self.builders.build(name, count=count, includes=includes, overrides=overrides)

    def resolve(self, value: Any) -> Any:
        """Resolve a placeholder string via secrets.resolve_placeholder().

        If value starts with ``secret:``, stores the resolved value for later masking.

        Args:
            value: The value to resolve. Non-string values returned as-is.

        Returns:
            Resolved value, or original value if not a string.
        """
        if not isinstance(value, str):
            return value
        is_secret = value.startswith("secret:")
        result = resolve_placeholder(value, self.config, manager=self)
        if is_secret and isinstance(result, str):
            self._secret_values.add(result)
        return result

    def mask(self, value: Any) -> Any:
        """Mask a value if it was resolved from a secret.

        Args:
            value: The value to check.

        Returns:
            ``"***"`` if the value is a secret value, else original value.
            None returns None. Non-string values return the original value.
        """
        if value is None:
            return None
        if isinstance(value, str) and value in self._secret_values:
            return "***"
        return value
