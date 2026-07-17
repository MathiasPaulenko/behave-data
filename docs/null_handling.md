# Null Handling

By default, behave-data converts common null markers to Python `None`. Empty cells stop being empty strings.

## Default null markers

These values are converted to `None`:

- `""` (empty string)
- `"null"`
- `"None"`
- `"N/A"`

## Example

```gherkin
| name:str | age:int? | city:str? |
| Alice    | 30       | NYC       |
| Bob      | null     | N/A       |
| Carol    |          |           |
```

Result:

```python
[
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": None, "city": None},
    {"name": "Carol", "age": None, "city": None},
]
```

## Configuring global null markers

Use `behave_data.yml`:

```yaml
null_markers:
  - ""
  - "null"
  - "None"
  - "N/A"
  - "nil"
  - "-"
```

Or in code:

```python
from behave_data import Config, typed_wrap

config = Config(null_markers={"", "null", "nil", "-"})
context.users = typed_wrap(context.table, config).typed_dicts()
```

## Per-column null markers

You can define different null markers for specific columns. This is useful when one column uses `-` for "not applicable" but another uses it as a real value.

In `behave_data.yml`:

```yaml
null_markers:
  - ""
  - "null"
  - "None"

null_markers_by_column:
  age:
    - ""
    - "N/A"
    - "unknown"
```

In code:

```python
from behave_data import Config

config = Config(
    null_markers={"", "null", "None"},
    null_markers_by_column={
        "age": {"", "N/A", "unknown"},
    },
)
```

## API

```python
from behave_data import is_null, resolve_null

is_null("N/A")  # True
is_null("real")  # False

resolve_null("N/A")  # None
resolve_null("real")  # "real"
```

Custom markers:

```python
is_null("TBD", frozenset({"TBD"}))  # True
```
