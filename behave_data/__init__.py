"""behave-data — Data management for Behave."""

from behave_tables import (
    ColumnMismatchError,
    TableLike,
    TableWrapper,
    wrap,
)

from behave_data.config import Config
from behave_data.diff import diff
from behave_data.errors import (
    BehaveDataError,
    BuilderNotFoundError,
    FixtureNotFoundError,
    LoaderNotFoundError,
    OptionalDependencyError,
    RawTableError,
    TableDiffError,
    TypeConversionError,
)
from behave_data.hooks import before_step_hook, setup_data
from behave_data.null import get_column_markers, is_null, resolve_null
from behave_data.patch import apply_patches, revert_patches
from behave_data.raw_table import RawTable, raw_table
from behave_data.typed_table import TypedTableWrapper, typed_wrap
from behave_data.types import TYPE_CONVERTERS, convert_cell, parse_column_header, register_type

__version__ = "0.1.0"

__all__ = [
    "BehaveDataError",
    "BuilderNotFoundError",
    "ColumnMismatchError",
    "Config",
    "FixtureNotFoundError",
    "LoaderNotFoundError",
    "OptionalDependencyError",
    "RawTable",
    "RawTableError",
    "TableDiffError",
    "TableLike",
    "TableWrapper",
    "TYPE_CONVERTERS",
    "TypeConversionError",
    "TypedTableWrapper",
    "apply_patches",
    "before_step_hook",
    "convert_cell",
    "diff",
    "get_column_markers",
    "is_null",
    "parse_column_header",
    "raw_table",
    "register_type",
    "resolve_null",
    "revert_patches",
    "setup_data",
    "typed_wrap",
    "wrap",
]
