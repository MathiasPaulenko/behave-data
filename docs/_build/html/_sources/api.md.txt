# API Reference

## typed_wrap

```python
from behave_data import typed_wrap

typed_wrap(table, config=None)
```

Wraps a Behave `Table` in `TypedTableWrapper`.

- `table`: a `behave.model.Table` or any `TableLike` object.
- `config`: optional `Config` instance.

Returns a `TypedTableWrapper`.

## raw_table

```python
from behave_data import raw_table

raw_table(table)
```

Wraps a table in `RawTable` for header-included access.

## TypedTableWrapper

```python
from behave_data import TypedTableWrapper

wrapper = TypedTableWrapper(table, config)
```

Methods:

- `typed_dicts()` → `list[dict[str, Any]]`
- `typed_objects(cls)` → `list[T]`
- `clean_headers()` → `list[str]`
- All `behave-tables` `TableWrapper` methods.

## DataManager

```python
from behave_data import DataManager, Config

dm = DataManager(Config())
```

### fixture

```python
dm.fixture(name, **overrides)
```

Get fixture data with optional overrides.

### build

```python
dm.build(name, count=1, overrides=None)
```

Build data. Returns a list if `count > 1`, otherwise a single dict.

### resolve

```python
dm.resolve(value)
```

Resolve a placeholder string. Non-string values pass through.

### mask

```python
dm.mask(value)
```

Return `"***"` if `value` is a resolved secret, else original value.

## FixtureRegistry

```python
from behave_data import FixtureRegistry, data_fixture

registry = FixtureRegistry()
registry.register("user", lambda: {"name": "Alice"})
```

`@data_fixture(name, scope="scenario", params=None)` decorator registers a fixture in the global registry.

## BuilderRegistry

```python
from behave_data import BuilderRegistry, data_builder

registry = BuilderRegistry()
registry.register("product", lambda o: {"name": "Widget", **o})
```

`@data_builder(name)` decorator registers a builder.

## Config

```python
from behave_data import Config

config = Config()
config = Config.from_file("behave_data.yml")
```

## diff

```python
from behave_data import diff

diff(expected, actual, ordered=True, ignore_columns=None, surplus_columns=True)
```

Raises `TableDiffError` if tables differ.

## resolve_placeholder

```python
from behave_data import resolve_placeholder

resolve_placeholder(value, config, manager=None)
```

Resolve `env:`, `file:`, `secret:`, `ref:` placeholders.

## register_type

```python
from behave_data import register_type

register_type("upper", lambda v: v.upper())
```

Register a custom type converter for typed table headers.

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

## Exceptions

- `BehaveDataError` — base exception
- `TypeConversionError` — invalid type conversion
- `TableDiffError` — table mismatch
- `ColumnMismatchError` — column mismatch in table operations
- `LoaderNotFoundError` — unknown loader schema
- `FixtureNotFoundError` — unknown fixture
- `BuilderNotFoundError` — unknown builder
- `OptionalDependencyError` — missing optional dependency
