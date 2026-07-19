# Migration Guide

If you are already using [`behave-tables`](https://github.com/MathiasPaulenko/behave-tables), moving to **behave-data** is straightforward. `behave-data` depends on `behave-tables` and re-exports its core APIs, so you can adopt features incrementally.

## Before you start

- `behave-data` requires Python 3.11+
- `behave-tables` is installed automatically as a dependency

## 1. Install behave-data

```bash
pip install behave-data
```

If you use YAML/Excel/SQL/HTTP, add the same extras:

```bash
pip install behave-data[yaml,excel,sql,http]
```

## 2. Update `features/environment.py`

Wire the behave-data hooks into Behave's lifecycle:

```python
from behave_data import (
    setup_data,
    before_feature_hook,
    before_scenario_hook,
    before_step_hook,
    after_scenario_hook,
)


def before_all(context):
    setup_data(context)


def before_feature(context, feature):
    before_feature_hook(context, feature)


def before_scenario(context, scenario):
    before_scenario_hook(context, scenario)


def before_step(context, step):
    before_step_hook(context, step)


def after_scenario(context, scenario):
    after_scenario_hook(context, scenario)
```

## 3. Replace `wrap()` with `typed_wrap()` for typed tables

`wrap()` still works for untyped table manipulation. For automatic type conversion and null resolution, use `typed_wrap()`:

```python
from behave_data import typed_wrap

# Before: all strings
users = wrap(context.table).as_dicts()
users[0]["age"]  # "30" (string)

# After: typed values
users = typed_wrap(context.table).typed_dicts()
users[0]["age"]  # 30 (int)
```

## 4. Add type annotations to headers

Change feature files from plain headers to typed headers:

```gherkin
# Before
| name | age |
| Alice| 30  |

# After
| name:str | age:int |
| Alice    | 30      |
```

Supported types: `str`, `int`, `float`, `bool`, `date`, `datetime`, and custom types registered with `register_type()`.

## 5. Handle null values

Empty cells and common markers (`"null"`, `"None"`, `"N/A"`) become `None` automatically.

Add `?` to nullable typed columns:

```gherkin
| age:int? |
| 30       |
|          |
```

Or configure custom markers in `behave_data.yml`:

```yaml
null_markers:
  - ""
  - "N/A"
  - "unknown"
```

## 6. Use dynamic Examples instead of static blocks

Replace static `Examples` with data loaded from CSV, JSON, YAML, Excel, SQL, or HTTP:

```gherkin
@load_examples:csv:features/data/users.csv
Scenario Outline: Create user
  Given a user with name "<name>" and email "<email>"

  Examples:
    | placeholder | placeholder |
```

## 7. Use fixtures and builders for reusable data

Move hard-coded test data into fixtures or builders:

```python
from behave_data import data_fixture


@data_fixture("admin_user")
def admin_user():
    return {"name": "Admin", "role": "admin"}
```

Then load it with a tag:

```gherkin
@needs_data:admin_user
Scenario: Admin can access dashboard
```

## 8. Keep using `behave-tables` methods

`behave-data` re-exports `wrap`, `TableWrapper`, `ColumnMismatchError`, and `TableLike`. All `behave-tables` methods such as `as_dicts()`, `as_models()`, `transpose()`, `to_csv()`, `find_row()`, `select()`, etc. remain available.

## What's next?

- [Quickstart](quickstart.md)
- [Typed Tables](typed_tables.md)
- [Configuration](configuration.md)
- [Fixtures](fixtures.md)
- [Builders](builders.md)
