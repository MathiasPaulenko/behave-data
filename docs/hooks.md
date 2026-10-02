# Behave Hooks

behave-data exposes hooks that you wire into Behave's lifecycle.

## Recommended environment.py

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

## setup_data

Initializes `context.data` as a `DataManager`, loads config from `behave_data.yml`, and applies patches.

```python
def setup_data(context, config=None)
```

Pass a custom config:

```python
from behave_data import Config


def before_all(context):
    setup_data(context, Config(null_markers={"", "n/a"}))
```

## before_feature_hook

Loads dynamic Examples for scenario outlines tagged with `@load_examples:`.

## before_scenario_hook

Processes declarative tags: `@needs_data`, `@with_fixture`, `@cleanup_after`.

## before_step_hook

Resolves `{placeholder}` patterns in the step's **table** and **doc string**.
The original step is never mutated — results are stored on the context:

- `context.resolved_table` → `{"headings": [...], "rows": [...]}` (or `None` when the step has no table)
- `context.resolved_text` → resolved doc string (or `None`)

Both attributes are reset on every step, so values never leak between steps.

> Placeholders in the step *text* itself (`Given I login as {user.name}`)
> are **not** resolved: Behave matches the step text to a step definition
> before `before_step` runs. Use table cells or doc strings instead.

## after_scenario_hook

Runs cleanup functions registered via `@cleanup_after` or `_behave_data_cleanup_funcs`.

## Placeholder resolution in steps

Placeholders use dot notation (`{obj.attr}`). Intermediate objects can be
objects with attributes, or plain dicts — dict keys are looked up first:

```python
from behave_data import data_fixture


@data_fixture("user")
def user():
    return {"name": "Alice", "email": "alice@example.com"}
```

Feature:

```gherkin
@needs_data:user
Scenario: Email via table
  Given a recipient table
    | email        |
    | {user.email} |
```

In the step, read the resolved copy:

```python
@given("a recipient table")
def step_recipient(context):
    email = context.resolved_table["rows"][0][0]  # "alice@example.com"
```

Attribute access also works — attach a `SimpleNamespace` or any object to
the context and `{user.email}` resolves through attributes.

## Manual hook usage

You can call hooks directly:

```python
from behave_data.hooks import before_step_hook

before_step_hook(context, step)
```
