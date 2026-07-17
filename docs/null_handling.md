# Null Handling

By default, behave-data converts common null markers to Python `None`. This means empty cells stop being empty strings.

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

## Configuring null markers

Create `behave_data.yml`:

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

## Per-column override

You can override markers per header using the `null` marker syntax in the column name. For more control, create a `Config` and pass it to `typed_wrap`:

```python
from behave_data import Config

config = Config(null_markers=frozenset({"", "N/A", "missing"}))
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
