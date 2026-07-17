"""behave-data — Data management for Behave."""

from behave_tables import (
    ColumnMismatchError,
    TableLike,
    TableWrapper,
    wrap,
)

from behave_data.builders import BuilderRegistry, data_builder
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
from behave_data.examples import load_examples_for_feature
from behave_data.fixtures import FixtureRegistry, data_fixture
from behave_data.hooks import (
    after_scenario_hook,
    before_feature_hook,
    before_scenario_hook,
    before_step_hook,
    setup_data,
)
from behave_data.manager import DataManager
from behave_data.null import get_column_markers, is_null, resolve_null
from behave_data.patch import apply_patches, revert_patches
from behave_data.raw_table import RawTable, raw_table
from behave_data.secrets import resolve_placeholder
from behave_data.tags import process_tags_after_scenario, process_tags_before_scenario
from behave_data.typed_table import TypedTableWrapper, typed_wrap
from behave_data.types import TYPE_CONVERTERS, convert_cell, parse_column_header, register_type

__version__ = "0.1.2"

__all__ = [
    "BehaveDataError",
    "BuilderNotFoundError",
    "BuilderRegistry",
    "ColumnMismatchError",
    "Config",
    "DataManager",
    "FixtureNotFoundError",
    "FixtureRegistry",
    "LoaderNotFoundError",
    "OptionalDependencyError",
    "RawTable",
    "after_scenario_hook",
    "before_feature_hook",
    "before_scenario_hook",
    "data_builder",
    "data_fixture",
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
    "load_examples_for_feature",
    "parse_column_header",
    "process_tags_after_scenario",
    "process_tags_before_scenario",
    "raw_table",
    "register_type",
    "resolve_null",
    "resolve_placeholder",
    "revert_patches",
    "setup_data",
    "typed_wrap",
    "wrap",
]
