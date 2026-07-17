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

Resolves placeholders in step text and table cells:

```gherkin
Given I login as {user.name}
```

If `context.user` exists with a `name` attribute, `{user.name}` is replaced.

## after_scenario_hook

Runs cleanup functions registered via `@cleanup_after` or `_behave_data_cleanup_funcs`.

## Placeholder resolution in steps

Placeholders use **attribute access** (`{obj.attr}`). The fixture must return an object with attributes, or you can attach a dict to the context and use `SimpleNamespace`:

```python
from types import SimpleNamespace
from behave_data import data_fixture

@data_fixture("user")
def user():
    return SimpleNamespace(name="Alice", email="alice@example.com")
```

Feature:

```gherkin
@needs_data:user
Scenario: Send email
  Given I send email to {user.email}
```

The step text becomes `I send email to alice@example.com` before matching.

Placeholders also work inside table cells:

```gherkin
@needs_data:user
Scenario: Email via table
  Given a recipient table
    | email          |
    | {user.email}   |
```

## Manual hook usage

You can call hooks directly:

```python
from behave_data.hooks import before_step_hook

before_step_hook(context, step)
```
