# Raw Tables

Sometimes a Behave table has no header, or you want to treat the header as data. `RawTable` gives you full access to all rows.

## When to use

- Tables verticales.
- Tablas donde la primera fila también es dato.
- Necesitas acceder a celdas como matriz de strings.

## Basic example

```gherkin
Scenario: Raw matrix
  Given a raw table
    | col1 | col2 |
    | a    | b    |
    | c    | d    |
```

```python
from behave_data import RawTable

@given("a raw table")
def step_raw(context):
    context.raw = RawTable(context.table)
```

`context.raw.rows` returns:

```python
[["col1", "col2"], ["a", "b"], ["c", "d"]]
```

The first row is the header, followed by all data rows.

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

## to_dicts with custom headers

```python
context.raw.to_dicts(["x", "y"])
# [{"x": "a", "y": "b"}, {"x": "c", "y": "d"}]
```

## Comparison

`RawTable` supports equality comparison:

```python
table1 = RawTable(context.table1)
table2 = RawTable(context.table2)
assert table1 == table2
```

`RawTable` is unhashable by design.
