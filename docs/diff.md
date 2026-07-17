# Table Diff

Compare expected vs actual tables with readable, Cucumber-style output.

`diff()` always raises `TableDiffError` when the tables differ. If you want to check whether they match without raising, catch the exception.

## Basic diff

```python
from behave_data import diff, TableDiffError

@then("the actual table matches expected")
def step_actual_matches(context):
    diff(context.expected_table, context.actual_table)
```

If tables differ, the raised `TableDiffError` contains output similar to:

```text
Tables were not identical:
      - | Alice | 30 |
      + | Bob | 30 |
```

## Check diff without failing

```python
from behave_data import diff, TableDiffError

@then("the tables match")
def step_check_diff(context):
    try:
        diff(context.expected_table, context.actual_table)
    except TableDiffError as exc:
        print("Tables differ:", exc)
        raise
```

## Ignore columns

```python
diff(
    context.expected_table,
    context.actual_table,
    ignore_columns=["created_at", "id"],
)
```

## Unordered comparison

```python
diff(context.expected_table, context.actual_table, ordered=False)
```

## Surplus columns

By default, extra columns in the actual table cause a diff. Disable with:

```python
diff(context.expected_table, context.actual_table, surplus_columns=False)
```

## Diff in features

```gherkin
Feature: Table comparison

  Scenario: Prices should match
    Given an expected price list
      | name:str | price:float |
      | Apple    | 1.50        |
    When the actual price list is
      | name:str | price:float |
      | Apple    | 1.50        |
    Then the prices should match
```

```python
from behave_data import diff

@given("an expected price list")
def step_expected(context):
    context.expected = context.table

@when("the actual price list is")
def step_actual(context):
    context.actual = context.table

@then("the prices should match")
def step_match(context):
    diff(context.expected, context.actual)
```

## Diff with list of dicts

`actual` can be a `list[dict]`, a single `dict`, or a table-like object. `list[list]` is **not** supported because headers are required.

```python
from behave_data import diff

expected = context.table
actual = [
    {"name": "Apple", "price": "1.50"},
]
diff(expected, actual)
```

## Diff an empty table

```python
from behave_data import diff

# actual is an empty list of dicts with expected headers
diff(context.expected_table, [])
```
