# API Reference

Quick reference with copy-pasteable examples.

## typed_wrap

```python
from behave_data import typed_wrap

products = typed_wrap(context.table).typed_dicts()
```

- `table`: a `behave.model.Table` or any `TableLike` object.
- `config`: optional `Config` instance.
- Returns a `TypedTableWrapper`.

## raw_table

```python
from behave_data import raw_table

raw = raw_table(context.table)
for row in raw.rows:
    print(row)
```

## TypedTableWrapper

```python
from behave_data import TypedTableWrapper

wrapper = TypedTableWrapper(context.table)

dicts = wrapper.typed_dicts()
objects = wrapper.typed_objects(Product)
headers = wrapper.clean_headers()
```

Also inherits all `behave-tables` methods: `as_dicts()`, `as_models()`, `transpose()`, `to_csv()`, etc.

## DataManager

```python
from behave_data import DataManager, Config

dm = DataManager(Config())
```

### fixture

```python
admin = dm.fixture("admin_user")
admin = dm.fixture("admin_user", email="override@example.com")
```

### build

```python
product = dm.build("product")
products = dm.build("product", count=3)
product = dm.build("product", overrides={"name": "Gadget"})
```

### resolve

```python
token = dm.resolve("env:API_TOKEN")
token = dm.resolve("file:secrets/token.txt")
token = dm.resolve("secret:API_TOKEN")
```

### mask

```python
token = dm.resolve("secret:API_TOKEN")
print(dm.mask(token))  # ***
```

## FixtureRegistry

```python
from behave_data import FixtureRegistry

registry = FixtureRegistry()
registry.register("user", lambda: {"name": "Alice"})
user = registry.get("user")
```

`@data_fixture(name, scope="scenario", params=None)` registers a fixture globally:

```python
from behave_data import data_fixture

@data_fixture("user")
def user():
    return {"name": "Alice"}
```

## BuilderRegistry

```python
from behave_data import BuilderRegistry

registry = BuilderRegistry()
registry.register("product", lambda o: {"name": "Widget", **o})
product = registry.build("product")
```

`@data_builder(name)` registers a builder globally:

```python
from behave_data import data_builder

@data_builder("product")
def product(overrides):
    return {"name": "Widget", **overrides}
```

## Config

```python
from behave_data import Config

config = Config()
config = Config.from_file("behave_data.yml")
```

## diff

```python
from behave_data import diff

diff(context.expected_table, context.actual_table)
diff(context.expected_table, context.actual_table, ordered=False)
diff(context.expected_table, context.actual_table, ignore_columns=["id"])
```

## resolve_placeholder

Low-level placeholder resolution. Normally you use `DataManager.resolve()`.

```python
from behave_data import resolve_placeholder, Config

cfg = Config(secret_path="secrets/")
value = resolve_placeholder("env:API_TOKEN", cfg)
```

## register_type

```python
from behave_data import register_type

register_type("upper", lambda v: v.upper())
```

Then use in tables:

```gherkin
| code:upper |
| abc        |
```

## Hooks

```python
from behave_data import (
    setup_data,
    before_feature_hook,
    before_scenario_hook,
    before_step_hook,
    after_scenario_hook,
)
```

Typical `environment.py`:

```python
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

## Exceptions

- `BehaveDataError` — base exception
- `TypeConversionError` — invalid type conversion
- `TableDiffError` — table mismatch
- `ColumnMismatchError` — column mismatch in table operations
- `LoaderNotFoundError` — unknown loader schema
- `FixtureNotFoundError` — unknown fixture
- `BuilderNotFoundError` — unknown builder
- `OptionalDependencyError` — missing optional dependency
