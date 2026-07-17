# Secrets

behave-data resolves sensitive values from different backends without hardcoding them in your feature files.

## Placeholder syntax

- `env:VAR_NAME` — read environment variable
- `file:path.txt` — read from file
- `secret:name` — resolve from configured secret backend
- plain text — returned as-is

## Environment variables

```gherkin
Scenario: Use API token
  Given I call the API with token "env:API_TOKEN"
```

```python
from behave_data import DataManager

dm = DataManager()
token = dm.resolve("env:API_TOKEN")
```

## Files

```python
dm = DataManager(config=Config(secret_path="secrets/"))
token = dm.resolve("file:api_token.txt")
```

`secret_path` is prepended to relative file paths.

## Secret backend

Configure the backend in `behave_data.yml`:

```yaml
secret_backend: env
```

Or in code:

```python
from behave_data import Config, DataManager

dm = DataManager(Config(secret_backend="env"))
```

## Backends

| Backend | Source | Extra |
|---------|--------|-------|
| `file` | Read from `secret_path` directory | — |
| `env`  | Read from environment variables | — |
| `vault` | HashiCorp Vault KV v2 | `[vault]` |
| `aws` | AWS Secrets Manager | `[aws]` |

### HashiCorp Vault

```python
from behave_data import Config, DataManager

dm = DataManager(Config(secret_backend="vault"))
value = dm.resolve("secret:my-secret")
```

Requires `VAULT_ADDR` and `VAULT_TOKEN` environment variables.

### AWS Secrets Manager

```python
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
