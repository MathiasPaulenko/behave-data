# behave-data

**Data management for [Behave](https://github.com/behave/behave) BDD framework.**

Typed data tables, readable diffs, dynamic Examples from external sources, reusable fixtures & builders, secret resolution with masking, and declarative tags — all with zero boilerplate in your `environment.py`.

Built on top of [behave-tables](https://github.com/MathiasPaulenko/behave-tables) for table manipulation.

## Features

- **Typed Tables** — Column type annotations (`name:str`, `age:int`, `active:bool`, `price:float`, `created:date`) with automatic conversion. No more everything-is-string.
- **Null Resolution** — Empty cells become `None`, not `""`. Configurable null markers (`""`, `"null"`, `"None"`, `"N/A"`), per-column overrides.
- **Table Diff** — Cucumber-style diff output with row/column mismatch detection. Clear, readable comparison of expected vs actual.
- **Raw Tables** — Access tables without header assumption. Vertical tables, transposed data, full control.
- **Dynamic Examples** — Load Examples from CSV, JSON, YAML, Excel, SQL, or HTTP APIs via `@load_examples:source` tags. Replace static Examples blocks with real data.
- **Fixtures** — Reusable data recipes with scoping, nesting (`ref:other`), and parametrization. Register with `@data_fixture` decorator.
- **Builders** — Construct test data with derived fields, overrides, and nesting. Register with `@data_builder` decorator.
- **Secrets** — Resolve `env:VAR`, `file:path`, `secret:name` placeholders. Multiple backends: file, env, HashiCorp Vault, AWS Secrets Manager. Automatic masking of resolved secrets.
- **Declarative Tags** — `@needs_data:name`, `@with_fixture:name`, `@cleanup_after` tags for automatic data setup/teardown. Less boilerplate in `environment.py`.
- **DataManager** — Unified access point for fixtures, builders, and secret resolution with automatic masking.
- **Behave Hooks** — `setup_data()`, `before_feature_hook()`, `before_scenario_hook()`, `before_step_hook()`, `after_scenario_hook()`. Placeholder resolution in table cells.

## Install

```bash
pip install behave-data
```

Optional dependencies for loaders and secret backends:

```bash
pip install behave-data[yaml]        # PyYAML for YAML loader
pip install behave-data[excel]       # openpyxl for Excel loader
pip install behave-data[sql]         # SQLAlchemy for SQL loader
pip install behave-data[http]        # requests for HTTP loader
pip install behave-data[vault]       # hvac for Vault secrets
pip install behave-data[aws]         # boto3 for AWS Secrets Manager
pip install behave-data[dev,yaml,excel]  # Development setup
```

## Quickstart

### 1. Setup

```python
# features/environment.py
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

### 2. Typed Tables

```python
# features/steps/typing.py
from behave_data import typed_wrap

class Car:
    def __init__(self, name: str, doors: int, price: float, electric: bool):
        self.name = name
        self.doors = doors
        self.price = price
        self.electric = electric

@then("the car should have")
def step_car(context):
    table = typed_wrap(context.table)
    cars = table.typed_objects(Car)
    for car in cars:
        assert car.doors == 4       # int, not "4"
        assert car.electric is True  # bool, not "true"
```

Feature file with typed headers:

```gherkin
Then the car should have
  | name:str | doors:int | price:float | electric:bool |
  | Tesla    | 4         | 79999.99    | true          |
  | BMW      | 4         | 55000.00    | false         |
```

### 3. Null Resolution

```gherkin
Then the users should be
  | name:str | age:int | city:str |
  | Alice    | 30      | NYC      |
  | Bob      |         |          |
  | Carol    | null    | N/A      |
```

```python
from behave_data import typed_wrap, is_null

@then("the users should be")
def step_users(context):
    table = typed_wrap(context.table)
    for row in table.typed_dicts():
        if row["age"] is None:  # empty cell -> None, not ""
            assert row["name"] in ("Bob", "Carol")
```

### 4. Table Diff

```python
from behave_data import diff

@then("the result should match")
def step_diff(context):
    expected = [["name", "age"], ["Alice", "30"], ["Bob", "25"]]
    actual = [list(r) for r in context.table.rows]
    result = diff(expected, actual)
    if result.has_diff:
        assert False, result.output  # Cucumber-style diff
```

### 5. Dynamic Examples

Load Examples from external sources instead of hardcoding them:

```gherkin
@load_examples:csv:features/data/users.csv
Scenario Outline: User login
  Given a user with name "<name>" and email "<email>"
  When they log in
  Then they see the dashboard

  Examples:
    | name | email |
    | old  | old   |
```

The CSV file replaces the Examples rows:

```csv
name,email
Alice,alice@example.com
Bob,bob@example.com
```

Supported sources: `csv:path`, `json:path`, `yaml:path`, `excel:path`, `sql:SELECT ...`, `GET https://api.example.com/users`.

### 6. Fixtures

```python
from behave_data import data_fixture

@data_fixture("admin_user")
def admin_user():
    return {"name": "Admin", "role": "admin", "email": "admin@example.com"}

@data_fixture("regular_user", params=["alice", "bob"])
def regular_user(param):
    return {"name": param, "role": "user"}

# Usage
dm = context.data
admin = dm.fixture("admin_user")
alice = dm.fixture("regular_user:alice")
```

### 7. Builders

```python
from behave_data import data_builder

@data_builder("user")
def user(overrides):
    return {"name": "Default", "email": "default@test.com", **overrides}

# Usage
dm = context.data
one = dm.build("user")                          # single user
three = dm.build("user", count=3)               # list of 3
custom = dm.build("user", overrides={"name": "Custom"})
```

### 8. Secrets & Masking

```python
# behave_data.yml
# secret_backend: env
# secret_path: secrets/

# In steps
dm = context.data
api_key = dm.resolve("env:API_KEY")         # from environment
db_pass = dm.resolve("file:db_password")    # from secrets/db_password
token = dm.resolve("secret:api_token")      # from configured backend

# Masking — secrets resolved via "secret:" are automatically masked
print(dm.mask(api_key))  # "***" if resolved from secret:, else original
```

Backends: `file` (default), `env`, `vault` (HashiCorp Vault via hvac), `aws` (AWS Secrets Manager via boto3).

### 9. Declarative Tags

```gherkin
@needs_data:admin_user
@with_fixture:test_config
@cleanup_after
Scenario: Admin can delete users
  Given an admin user
  When they delete a user
  Then the user is gone
```

```python
# Tags are processed automatically by before_scenario_hook / after_scenario_hook
# context.admin_user is available via @needs_data
# context.test_config is available via @with_fixture
# Cleanup functions are executed after the scenario
```

## API Reference

### Core

| Name | Description |
|------|-------------|
| `Config` | Configuration dataclass with `from_file()` |
| `DataManager` | Unified access: fixtures, builders, secrets, masking |
| `setup_data(context, config?)` | Initialize behave-data |
| `apply_patches()` / `revert_patches()` | Patch/unpatch Behave table classes |

### Typed Tables

| Name | Description |
|------|-------------|
| `TypedTableWrapper` | Table wrapper with typed conversion |
| `typed_wrap(table)` | Wrap a Behave table with type annotations |
| `parse_column_header(header)` | Parse `name:type` headers |
| `convert_cell(value, type_name)` | Convert a cell value to a type |
| `register_type(name, converter)` | Register a custom type converter |
| `TYPE_CONVERTERS` | Dict of registered type converters |

### Null Handling

| Name | Description |
|------|-------------|
| `is_null(value, markers?)` | Check if a value is a null marker |
| `resolve_null(value, markers?)` | Convert null markers to `None` |
| `get_column_markers(column, config)` | Get null markers for a column |

### Diff

| Name | Description |
|------|-------------|
| `diff(expected, actual)` | Compare two tables, returns `DiffResult` |

### Raw Tables

| Name | Description |
|------|-------------|
| `RawTable` | Access table without header assumption |
| `raw_table(table)` | Create a RawTable from a Behave table |

### Loaders

| Name | Description |
|------|-------------|
| `load(source, config?)` | Load data from CSV, JSON, YAML, Excel, SQL, HTTP |

### Examples

| Name | Description |
|------|-------------|
| `load_examples_for_feature(feature, config)` | Load dynamic Examples for a feature |

### Fixtures & Builders

| Name | Description |
|------|-------------|
| `FixtureRegistry` | Registry for fixtures |
| `data_fixture(name, scope?, params?)` | Decorator to register a fixture |
| `BuilderRegistry` | Registry for builders |
| `data_builder(name)` | Decorator to register a builder |

### Secrets

| Name | Description |
|------|-------------|
| `resolve_placeholder(value, config?, manager?)` | Resolve `env:`, `file:`, `ref:`, `secret:` placeholders |
| `DataManager.resolve(value)` | Resolve via DataManager (tracks secrets for masking) |
| `DataManager.mask(value)` | Mask a value if it was resolved from a secret |

### Hooks

| Name | Description |
|------|-------------|
| `before_feature_hook(context, feature)` | Load dynamic Examples |
| `before_scenario_hook(context, scenario)` | Process declarative tags |
| `before_step_hook(context, step)` | Resolve `{placeholder}` in table cells |
| `after_scenario_hook(context, scenario)` | Execute cleanup functions |

### Tags

| Name | Description |
|------|-------------|
| `process_tags_before_scenario(context, scenario)` | Process `@needs_data`, `@with_fixture`, `@cleanup_after` |
| `process_tags_after_scenario(context, scenario)` | Execute cleanup functions |

### Errors

| Name | Description |
|------|-------------|
| `BehaveDataError` | Base exception |
| `TypeConversionError` | Type conversion failure |
| `TableDiffError` | Table diff mismatch |
| `RawTableError` | Raw table access error |
| `FixtureNotFoundError` | Fixture not registered |
| `BuilderNotFoundError` | Builder not registered |
| `LoaderNotFoundError` | No loader for source |
| `OptionalDependencyError` | Optional dependency missing |

## Migration from behave-tables

`behave-data` depends on `behave-tables` and extends it. If you're already using `behave-tables`:

1. `pip install behave-data` — `behave-tables` comes as a dependency.
2. Replace `from behave_tables import wrap, TableWrapper` with `from behave_data import wrap, TableWrapper` — same API, re-exported.
3. Use `typed_wrap()` instead of `wrap()` for typed column conversion.
4. Add `setup_data(context)` in `before_all()` to enable hooks, fixtures, builders, and secrets.
5. Optionally add `before_feature_hook`, `before_scenario_hook`, `before_step_hook`, and `after_scenario_hook` for full integration.

All `behave-tables` APIs (`as_dicts`, `as_models`, `transpose`, `to_csv`, `to_json`, `find_row`, `select`, etc.) are available through `behave-data` via the re-exported `TableWrapper` and `wrap()`.

## Configuration

Create a `behave_data.yml` file in your project root:

```yaml
null_markers: ["", "null", "None", "N/A"]
null_markers_by_column:
  age: ["", "unknown"]
secret_backend: env
secret_path: secrets/
load_base_dir: features/data/
db_connections:
  default: sqlite:///test.db
```

## License

MIT
