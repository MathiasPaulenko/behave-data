"""Tests for behave_data.errors."""

from __future__ import annotations

import logging

import pytest

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


class TestBehaveDataError:
    def test_is_exception(self) -> None:
        assert issubclass(BehaveDataError, Exception)

    def test_can_be_raised(self) -> None:
        with pytest.raises(BehaveDataError, match="something"):
            raise BehaveDataError("something")


class TestTypeConversionError:
    def test_constructs_with_attrs(self) -> None:
        cause = ValueError("bad number")
        err = TypeConversionError("doors", "abc", "int", cause)
        assert err.column == "doors"
        assert err.value == "abc"
        assert err.target_type == "int"
        assert err.cause is cause

    def test_message_format(self) -> None:
        cause = ValueError("bad number")
        err = TypeConversionError("doors", "abc", "int", cause)
        msg = str(err)
        assert "doors" in msg
        assert "'abc'" in msg
        assert "int" in msg
        assert "bad number" in msg

    def test_inherits_behave_data_error(self) -> None:
        assert issubclass(TypeConversionError, BehaveDataError)

    def test_preserves_cause_exception(self) -> None:
        cause = ValueError("invalid literal")
        err = TypeConversionError("price", "xyz", "float", cause)
        assert isinstance(err.cause, ValueError)
        assert str(err.cause) == "invalid literal"


class TestTableDiffError:
    def test_constructs_with_diff_output(self) -> None:
        err = TableDiffError("some diff output")
        assert err.diff_output == "some diff output"

    def test_message_is_diff_output(self) -> None:
        err = TableDiffError("  | name | age |\n- | Alice | 30 |")
        assert str(err) == "  | name | age |\n- | Alice | 30 |"

    def test_inherits_assertion_error(self) -> None:
        assert issubclass(TableDiffError, AssertionError)

    def test_catchable_as_assertion_error(self) -> None:
        with pytest.raises(AssertionError):
            raise TableDiffError("diff")

    def test_inherits_behave_data_error(self) -> None:
        assert issubclass(TableDiffError, BehaveDataError)

    def test_catchable_as_behave_data_error(self) -> None:
        with pytest.raises(BehaveDataError):
            raise TableDiffError("diff")

    def test_has_diff_output_attribute(self) -> None:
        err = TableDiffError("output")
        assert hasattr(err, "diff_output")


class TestFixtureNotFoundError:
    def test_constructs_with_name(self) -> None:
        err = FixtureNotFoundError("standard_user")
        assert err.name == "standard_user"

    def test_message_contains_name(self) -> None:
        err = FixtureNotFoundError("admin_user")
        assert "admin_user" in str(err)

    def test_inherits_behave_data_error(self) -> None:
        assert issubclass(FixtureNotFoundError, BehaveDataError)


class TestBuilderNotFoundError:
    def test_constructs_with_name(self) -> None:
        err = BuilderNotFoundError("user")
        assert err.name == "user"

    def test_message_contains_name(self) -> None:
        err = BuilderNotFoundError("order")
        assert "order" in str(err)

    def test_inherits_behave_data_error(self) -> None:
        assert issubclass(BuilderNotFoundError, BehaveDataError)


class TestLoaderNotFoundError:
    def test_constructs_with_source(self) -> None:
        err = LoaderNotFoundError("unknown.csv")
        assert err.source == "unknown.csv"

    def test_message_contains_source(self) -> None:
        err = LoaderNotFoundError("bad.source")
        assert "bad.source" in str(err)

    def test_inherits_behave_data_error(self) -> None:
        assert issubclass(LoaderNotFoundError, BehaveDataError)


class TestOptionalDependencyError:
    def test_constructs_with_attrs(self) -> None:
        err = OptionalDependencyError("pyyaml", "YAML loading", "pip install behave-data[yaml]")
        assert err.package == "pyyaml"

    def test_message_contains_package_and_install_cmd(self) -> None:
        err = OptionalDependencyError("pandas", "to_pandas()", "pip install behave-data[pandas]")
        msg = str(err)
        assert "pandas" in msg
        assert "pip install behave-data[pandas]" in msg

    def test_inherits_behave_data_error(self) -> None:
        assert issubclass(OptionalDependencyError, BehaveDataError)


class TestRawTableError:
    def test_inherits_behave_data_error(self) -> None:
        assert issubclass(RawTableError, BehaveDataError)

    def test_can_be_raised(self) -> None:
        with pytest.raises(RawTableError, match="fail"):
            raise RawTableError("fail")


class TestLogger:
    def test_logger_has_null_handler(self) -> None:
        log = logging.getLogger("behave_data")
        handler_types = [type(h).__name__ for h in log.handlers]
        assert "NullHandler" in handler_types

    def test_logger_name(self) -> None:
        log = logging.getLogger("behave_data")
        assert log.name == "behave_data"
