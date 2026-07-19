# Configuration

behave-data can be configured via `behave.ini` `[userdata]`, a YAML/JSON file, or directly in code.

## behave.ini (recommended)

Use Behave's native `[userdata]` section with `behave_data.` prefixed keys — no extra files and no collisions with other userdata:

```ini
# behave.ini
[userdata]
behave_data.null_markers = ,null,None,N/A
behave_data.secret_backend = env
behave_data.secret_path = secrets/
behave_data.load_base_dir = features/data/
```

`setup_data(context)` reads `context.config.userdata` automatically. No extra code needed.

### Complex options

Dict-valued options use JSON strings in `[userdata]`:

```ini
[userdata]
behave_data.null_markers = ,null,None,N/A
behave_data.secret_backend = env
behave_data.null_markers_by_column = {"phone": ["N/A", "null"]}
behave_data.db_connections = {"default": "sqlite:///test.db"}
behave_data.type_overrides = {"age": "int"}
```

## YAML file

Create a `behave_data.yml` in your project root (requires `pip install behave-data[yaml]`):

```yaml
null_markers:
  - ""
  - "null"
  - "None"
  - "N/A"

null_markers_by_column:
  phone:
    - N/A
    - null

secret_backend: env
secret_path: secrets/
load_base_dir: features/data/
db_connections:
  default: sqlite:///test.db
```

## JSON file

```json
{
  "null_markers": ["", "null", "None", "N/A"],
  "secret_backend": "env",
  "secret_path": "secrets/",
  "load_base_dir": "features/data/"
}
```

## In code

```python
from behave_data import Config

config = Config(
    null_markers=frozenset({"", "null", "N/A"}),
    secret_backend="env",
    secret_path="secrets/",
    load_base_dir="features/data/",
)
```

## Configuration priority

`setup_data(context)` resolves config in this order:

1. **Explicit parameter** — `setup_data(context, my_config)`
2. **`behave.ini` `[userdata]`** — if any `behave_data.*` keys are present in `context.config.userdata`
3. **`behave_data.yml`** — fallback file

## Options

| `behave.ini` key                    | YAML key                 | Default                       | Type            | Description                         |
|-------------------------------------|--------------------------|-------------------------------|-----------------|-------------------------------------|
| `behave_data.null_markers`          | `null_markers`           | `{"", "null", "None", "N/A"}` | comma-separated | Values converted to `None`          |
| `behave_data.null_markers_by_column`| `null_markers_by_column` | `{}`                          | JSON string     | Per-column null marker overrides    |
| `behave_data.secret_backend`        | `secret_backend`         | `"file"`                      | string          | Backend for `secret:` placeholders  |
| `behave_data.secret_path`           | `secret_path`            | `"secrets/"`                  | string          | Base path for `file:` secrets       |
| `behave_data.load_base_dir`         | `load_base_dir`          | `"features/data/"`            | string          | Base path for dynamic Examples      |
| `behave_data.db_connections`        | `db_connections`         | `{}`                          | JSON string     | Named database connection strings   |
| `behave_data.type_overrides`        | `type_overrides`         | `{}`                          | JSON string     | Per-column type overrides           |

## Loading config manually

```python
from behave_data import Config

# From behave.ini userdata
config = Config.from_userdata(context.config.userdata)

# From file
config = Config.from_file("behave_data.yml")
```

If the file does not exist, a default `Config()` is returned.

## Passing config to setup_data

```python
from behave_data import setup_data, Config

def before_all(context):
    setup_data(context, Config.from_file("config/behave_data.yml"))
```

## Passing config to typed_wrap

```python
from behave_data import typed_wrap, Config

config = Config(null_markers=frozenset({"", "missing"}))
result = typed_wrap(context.table, config).typed_dicts()
```
