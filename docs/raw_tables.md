# Raw Tables

Sometimes a Behave table has no header, or you want to treat the first row as data too. `RawTable` gives you full access to **all rows** as a plain matrix of strings.

## When to use

- Vertical tables where the first column is a label.
- Tables without a header row.
- Any time you need the raw cell matrix before typed conversion.

## Basic example

```gherkin
Scenario: Raw matrix
  Given a raw table
    | col1 | col2 |
    | a    | b    |
    | c    | d    |
```

```python
from behave_data import RawTable, raw_table

@given("a raw table")
def step_raw(context):
    context.raw = raw_table(context.table)
```

`context.raw.rows` returns every row, including the header:

```python
[["col1", "col2"], ["a", "b"], ["c", "d"]]
```

## Access rows

```python
context.raw.rows      # all rows including header
context.raw.raw_rows  # alias
len(context.raw)      # number of rows (including header)
```

Index a row:

```python
context.raw[0]  # ["col1", "col2"]
context.raw[1]  # ["a", "b"]
```

## Convert with custom headers

Use `to_dicts()` when you want to name the columns yourself:

```python
context.raw.to_dicts(["x", "y"])
# [{"x": "a", "y": "b"}, {"x": "c", "y": "d"}]
```

## Raw table without header

```gherkin
Scenario: No header
  Given a raw table
    | 2024-01-15 | 100 |
    | 2024-06-30 | 200 |
```

```python
@given("a raw table")
def step_raw(context):
    raw = raw_table(context.table)
    assert raw.rows == [
        ["2024-01-15", "100"],
        ["2024-06-30", "200"],
    ]
```

## Comparison

`RawTable` supports equality comparison:

```python
from behave_data import RawTable

table1 = RawTable(context.table1)
table2 = RawTable(context.table2)
assert table1 == table2
```

`RawTable` is unhashable by design.
