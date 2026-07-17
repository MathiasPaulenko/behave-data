# Configuration

behave-data can be configured via a YAML or JSON file, or directly in code.

## behave_data.yml

Create a `behave_data.yml` in the root of your project:

```yaml
null_markers:
  - ""
  - "null"
  - "None"
  - "N/A"
  - "n/a"

secret_backend: file
secret_path: secrets/
load_base_dir: features/data/
```

## behave_data.json

```json
{
  "null_markers": ["", "null", "None", "N/A"],
  "secret_backend": "file",
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

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `null_markers` | `{"", "null", "None", "N/A"}` | Values converted to `None` |
| `secret_backend` | `"file"` | Backend for `secret:` placeholders |
| `secret_path` | `"secrets/"` | Base path for `file:` secrets |
| `load_base_dir` | `"features/data/"` | Base path for dynamic Examples |

## Loading config manually

```python
from behave_data import Config

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
