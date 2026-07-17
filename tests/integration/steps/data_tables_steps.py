"""Integration steps for behave-data MVP."""

from __future__ import annotations

from behave import given, then, when

from behave_data import (
    RawTable,
    TableDiffError,
    TypedTableWrapper,
    diff,
)


@given("a table with typed columns")
def step_typed_columns(context):
    context.typed = TypedTableWrapper(context.table).typed_dicts()


@then("the typed dicts should have correct types")
def step_check_types(context):
    rows = context.typed
    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    assert isinstance(rows[0].get("age", rows[0].get("doors")), int)
    if "age" in rows[0]:
        assert rows[0]["age"] == 30
        assert rows[0]["active"] is True
        assert rows[1]["active"] is False
    if "doors" in rows[0]:
        assert rows[0]["doors"] == 3
        assert isinstance(rows[0]["price"], float)
        assert rows[0]["active"] is True
        assert rows[1]["active"] is False


@given("a table with null markers")
def step_null_markers(context):
    context.typed = TypedTableWrapper(context.table).typed_dicts()


@given("a table with nullable columns")
def step_nullable_columns(context):
    context.typed = TypedTableWrapper(context.table).typed_dicts()


@then("null cells should be resolved to None")
def step_check_nulls(context):
    rows = context.typed
    assert rows[0]["name"] == "Alice"
    if "age" in rows[0]:
        assert rows[0]["age"] == 30
    if "doors" in rows[0]:
        assert rows[0]["doors"] == 3
    if "city" in rows[0]:
        assert rows[0]["city"] == "NYC"
    # Second row has null markers — check which columns are None
    if rows[1]["name"] == "Bob":
        # nullable_types.feature: name is "Bob", doors is None
        assert rows[1]["doors"] is None
    else:
        # null_handling/data_tables: name is null, age is None
        assert rows[1]["name"] is None
        if "age" in rows[1]:
            assert rows[1]["age"] is None
        if "doors" in rows[1]:
            assert rows[1]["doors"] is None
        if "city" in rows[1]:
            assert rows[1]["city"] is None


@given("a table without assuming header")
def step_raw_table(context):
    context.raw = RawTable(context.table)


@then("the raw table should have {n:d} rows total")
def step_check_raw_count(context, n):
    assert len(context.raw) == n


@given("an expected table")
def step_expected_table(context):
    context.expected_table = context.table


@when("the actual table differs")
def step_actual_table(context):
    context.actual_table = context.table


@when("the actual table is the same")
def step_actual_same(context):
    context.actual_table = context.table


@then("the diff should raise an error")
def step_check_diff_error(context):
    try:
        diff(context.expected_table, context.actual_table)
        raise AssertionError("Expected TableDiffError was not raised")
    except TableDiffError:
        pass


@then("the diff should not raise an error")
def step_check_diff_no_error(context):
    diff(context.expected_table, context.actual_table)
