"""Custom exceptions for behave-data."""

from __future__ import annotations

import logging

logger = logging.getLogger("behave_data")
logger.addHandler(logging.NullHandler())


class BehaveDataError(Exception):
    """Base class for all behave-data errors."""


class TypeConversionError(BehaveDataError):
    """Raised when a cell value cannot be converted to the target type.

    Attributes:
        column: The column name where the conversion failed.
        value: The original value that could not be converted.
        target_type: The name of the target type.
        cause: The underlying exception that caused the failure.
    """

    def __init__(self, column: str, value: object, target_type: str, cause: Exception) -> None:
        self.column = column
        self.value = value
        self.target_type = target_type
        self.cause = cause
        super().__init__(
            f"Cannot convert column '{column}' value {value!r} to {target_type}: {cause}"
        )


class TableDiffError(BehaveDataError, AssertionError):
    """Raised when two tables are not identical.

    Inherits from both ``BehaveDataError`` and ``AssertionError`` so that
    ``except BehaveDataError`` catches it, and Behave treats it as a test
    failure.

    Attributes:
        diff_output: The human-readable diff string.
    """

    def __init__(self, diff_output: str) -> None:
        self.diff_output = diff_output
        super().__init__(diff_output)


class FixtureNotFoundError(BehaveDataError):
    """Raised when a requested fixture is not registered.

    Attributes:
        name: The fixture name that was not found.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Fixture '{name}' not registered.")


class BuilderNotFoundError(BehaveDataError):
    """Raised when a requested builder is not registered.

    Attributes:
        name: The builder name that was not found.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Builder '{name}' not registered.")


class LoaderNotFoundError(BehaveDataError):
    """Raised when no loader is found for a given source.

    Attributes:
        source: The source string that could not be matched to a loader.
    """

    def __init__(self, source: str) -> None:
        self.source = source
        super().__init__(f"No loader found for source: {source!r}")


class OptionalDependencyError(BehaveDataError):
    """Raised when an optional dependency is required but not installed.

    Attributes:
        package: The name of the missing package.
        feature: The feature that requires the package.
        install_cmd: The command to install the package.
    """

    def __init__(self, package: str, feature: str, install_cmd: str) -> None:
        self.package = package
        self.feature = feature
        self.install_cmd = install_cmd
        super().__init__(f"{package} is required for {feature}. Install it with: {install_cmd}")


class RawTableError(BehaveDataError):
    """Raised when raw table operations fail."""
