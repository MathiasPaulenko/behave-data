# Configuration

behave-data can be configured via `behave.ini` `[userdata]`, a YAML/JSON file, or directly in code.

## behave.ini (recommended)

Use Behave's native `[userdata]` section — no extra files:

```ini
# behave.ini
[userdata]
null_markers = ,null,None,N/A
secret_backend = env
secret_path = secrets/
load_base_dir = features/data/
```

`setup_data(context)` reads `context.config.userdata` automatically. No extra code needed.

### Complex options

Dict-valued options use JSON strings in `[userdata]`:

```ini
[userdata]
null_markers = ,null,None,N/A
secret_backend = env
null_markers_by_column = {"phone": ["N/A", "null"]}
db_connections = {"default": "sqlite:///test.db"}
type_overrides = {"age": "int"}
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
2. **`behave.ini` `[userdata]`** — if any known keys are present in `context.config.userdata`
3. **`behave_data.yml`** — fallback file

## Options

| Option | Default | Type | Description |
|--------|---------|------|-------------|
| `null_markers` | `{"", "null", "None", "N/A"}` | comma-separated | Values converted to `None` |
| `null_markers_by_column` | `{}` | JSON string | Per-column null marker overrides |
| `secret_backend` | `"file"` | string | Backend for `secret:` placeholders |
| `secret_path` | `"secrets/"` | string | Base path for `file:` secrets |
| `load_base_dir` | `"features/data/"` | string | Base path for dynamic Examples |
| `db_connections` | `{}` | JSON string | Named database connection strings |
| `type_overrides` | `{}` | JSON string | Per-column type overrides |

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
