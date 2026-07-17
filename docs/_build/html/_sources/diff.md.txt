# Table Diff

Compare expected vs actual tables with readable output.

## Basic diff

In your step definitions:

```python
from behave_data import diff, TableDiffError

@then("the actual table matches expected")
def step_actual_matches(context):
    diff(context.expected_table, context.actual_table)
```

If tables differ, `diff` raises `TableDiffError` with output like:

```text
Expected | Actual
  name   | name
- Alice  | + Bob
```

## Diff with raise_on_diff behavior

`diff()` raises on mismatch. If you want to check the result instead, catch the exception:

```python
from behave_data import diff, TableDiffError

def step_check_diff(context):
    try:
        diff(context.expected_table, context.actual_table)
        return True
    except TableDiffError:
        return False
```

## Ignore columns

Ignore one or more columns from comparison:

```python
diff(
    context.expected_table,
    context.actual_table,
    ignore_columns=["created_at", "id"],
)
```

## Unordered comparison

Rows can be in any order:

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
      | name  | price |
      | Apple | 1.50  |
    When the actual price list is
      | name  | price |
      | Apple | 1.50  |
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

Actual can also be a list of dicts:

```python
expected = context.table
actual = [
    {"name": "Apple", "price": "1.50"},
]
diff(expected, actual)
```

## Diff empty tables

```python
diff([["name"]], [])
```
