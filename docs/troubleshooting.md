# Troubleshooting

Common issues and how to fix them.

## Type conversion errors

**Symptom:**

```text
TypeConversionError: Cannot convert 'old' to int for column 'age'
```

**Cause:** The cell value cannot be converted to the type in the header.

**Fix:**

- Use `age:int?` if the column can be empty.
- Add custom markers in `behave_data.yml` if `N/A` or `-` should mean `None`.

```yaml
null_markers:
  - ""
  - "N/A"
  - "-"
```

## diff raises `ValueError: Cannot diff list[list]`

**Cause:** `diff` needs headers. A plain `list[list]` does not have them.

**Fix:** Use a `list[dict]` or a Behave `Table`:

```python
diff(context.expected_table, [{"name": "Alice"}])
```

## `@needs_data` fixture not on context

**Symptom:**

```python
context.admin_user  # AttributeError
```

**Cause:** The hook `before_scenario_hook` is not wired in `environment.py`.

**Fix:** Add all behave-data hooks to `features/environment.py`:

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

## Placeholders not replaced in step text

**Symptom:** `Given I send email to {user.email}` does not replace `{user.email}`.

**Cause:** `_resolve_placeholders` uses attribute access (`hasattr`/`getattr`). A plain `dict` does not expose keys as attributes.

**Fix:** Return a `SimpleNamespace`, a dataclass, or attach the object to `context`:

```python
from types import SimpleNamespace
from behave_data import data_fixture

@data_fixture("user")
def user():
    return SimpleNamespace(email="alice@example.com")
```

## `@load_examples` not loading data

**Symptom:** The scenario outline still runs with the original `Examples` rows.

**Cause:** `before_feature_hook` is missing or the tag is not on the `Scenario Outline`.

**Fix:**

- Check `before_feature_hook(context, feature)` is in `environment.py`.
- Make sure the tag is on the `Scenario Outline`, not the `Feature`.
- Keep an empty `Examples:` block; rows are replaced at runtime.

## Optional dependency errors

**Symptom:**

```text
OptionalDependencyError: pyyaml is required for YAML config loading
```

**Fix:** Install the required extra:

```bash
pip install behave-data[yaml]
```

## Secrets not masked

**Symptom:** `context.data.mask(secret)` returns the real value instead of `"***"`.

**Cause:** Only values resolved through `secret:` are masked. `env:` and `file:` are not treated as secrets unless you resolve them with `secret:` and the right backend.

**Fix:** Use `secret:` placeholders and `secret_backend: env` or `secret_backend: file`:

```yaml
secret_backend: env
```

```gherkin
| token:str        |
| secret:API_TOKEN |
```

## Circular fixture reference

**Symptom:**

```text
BehaveDataError: Circular fixture reference: user
```

**Cause:** A fixture contains `ref:<name>` that eventually points back to itself.

**Fix:** Remove or rename the self-reference.

## `typed_objects` fails

**Symptom:**

```text
TypeError: Product.__init__() got an unexpected keyword argument 'active'
```

**Cause:** The class fields do not match the table columns.

**Fix:** Use `clean_headers()` to see exact column names, or use a dataclass:

```python
from dataclasses import dataclass

@dataclass
class Product:
    name: str
    price: float
    active: bool
```

## Pages not updating after deploy

**Cause:** GitHub Pages caches content and workflows can take a minute to deploy.

**Fix:**

- Check the `Docs` workflow in the Actions tab.
- Wait 30-60 seconds after the workflow completes.
- Clear browser cache or open the page in an incognito window.
