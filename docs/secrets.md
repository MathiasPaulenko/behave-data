# Secrets

behave-data resolves sensitive values from different backends without hardcoding them in your feature files.

## Placeholder syntax

- `env:VAR_NAME` — read environment variable
- `file:path.txt` — read from file
- `secret:name` — resolve from configured secret backend
- `ref:fixture_name` — resolve another fixture
- plain text — returned as-is

## Environment variables

```bash
export API_TOKEN=abc123
```

```python
from behave_data import DataManager

dm = DataManager()
token = dm.resolve("env:API_TOKEN")
# "abc123"
```

In a feature:

```gherkin
Scenario: Use API token
  Given I call the API with token "env:API_TOKEN"
```

## Files

`secrets/api_token.txt`:

```text
abc123
```

```python
from behave_data import Config, DataManager

dm = DataManager(config=Config(secret_path="secrets/"))
token = dm.resolve("file:api_token.txt")
# "abc123"
```

`secret_path` is prepended to relative file paths.

## Secret backend

The `secret:` placeholder delegates to the configured backend. Set it in `behave_data.yml`:

```yaml
secret_backend: env
```

Or in code:

```python
from behave_data import Config, DataManager

dm = DataManager(Config(secret_backend="env"))
```

## Backends

| Backend | Source                          | Extra     |
|---------|---------------------------------|-----------|
| `file`  | Read from `secret_path` dir     | —         |
| `env`   | Read environment variables      | —         |
| `vault` | HashiCorp Vault KV v2           | `[vault]` |
| `aws`   | AWS Secrets Manager             | `[aws]`   |

With `secret_backend: env`:

```bash
export API_TOKEN=abc123
```

```python
dm.resolve("secret:API_TOKEN")  # "abc123"
```

With `secret_backend: file`:

```text
# secrets/API_TOKEN
abc123
```

```python
dm.resolve("secret:API_TOKEN")  # "abc123"
```

### HashiCorp Vault

```python
from behave_data import Config, DataManager

dm = DataManager(Config(secret_backend="vault"))
value = dm.resolve("secret:my-secret")
```

Requires `VAULT_ADDR` and `VAULT_TOKEN` environment variables.

### AWS Secrets Manager

```python
from behave_data import Config, DataManager

dm = DataManager(Config(secret_backend="aws"))
value = dm.resolve("secret:my-secret")
```

Uses boto3 default credentials.

## Masking secrets

Values resolved via `secret:` are automatically masked by `DataManager.mask()`:

```python
value = dm.resolve("secret:API_TOKEN")  # "abc123"
masked = dm.mask(value)  # "***"
```

This is useful when printing or logging.

## Using in tables

```gherkin
| name:str | token:str      |
| Alice    | secret:TOKEN_A |
| Bob      | secret:TOKEN_B |
```

```python
from behave_data import typed_wrap

users = typed_wrap(context.table).typed_dicts()
for user in users:
    token = context.data.resolve(user["token"])
    print(context.data.mask(token))  # ***
```

## Reference to fixture

```python
value = dm.resolve("ref:admin_user")
# Resolves the admin_user fixture
```

## Passthrough for non-strings

Integers, lists, and other non-string values are returned unchanged:

```python
dm.resolve(42)  # 42
dm.resolve([1, 2, 3])  # [1, 2, 3]
```
