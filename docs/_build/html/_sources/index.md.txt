---
hide-toc: true
---

# behave-data

```{image} _static/logo.svg
:alt: behave-data logo
:width: 120px
:align: center
```

**Data management for [Behave](https://github.com/behave/behave) BDD framework.**

Typed data tables, readable diffs, dynamic Examples from external sources, reusable fixtures & builders, secret resolution with masking, and declarative tags — all with zero boilerplate in your `environment.py`.

Built on top of [behave-tables](https://github.com/MathiasPaulenko/behave-tables) for table manipulation.

## What you get

- **Typed Tables** — Column type annotations (`name:str`, `age:int`, `active:bool`, `price:float`, `created:date`) with automatic conversion.
- **Null Resolution** — Empty cells become `None`, not `""`. Configurable null markers.
- **Table Diff** — Cucumber-style diff output with row/column mismatch detection.
- **Raw Tables** — Access tables without header assumption.
- **Dynamic Examples** — Load Examples from CSV, JSON, YAML, Excel, SQL, or HTTP APIs.
- **Fixtures** — Reusable data recipes with scoping, nesting, and parametrization.
- **Builders** — Construct test data with derived fields and overrides.
- **Secrets** — Resolve `env:VAR`, `file:path`, `secret:name` placeholders. Multiple backends.
- **Declarative Tags** — `@needs_data:name`, `@with_fixture:name`, `@cleanup_after`.
- **DataManager** — Unified access point for fixtures, builders, and secret resolution.

## Install

```bash
pip install behave-data
```

Optional dependencies:

```bash
pip install behave-data[yaml]    # PyYAML for YAML loader
pip install behave-data[excel]   # openpyxl for Excel loader
pip install behave-data[sql]     # SQLAlchemy for SQL loader
pip install behave-data[http]    # requests for HTTP loader
pip install behave-data[vault]   # hvac for Vault secrets
pip install behave-data[aws]     # boto3 for AWS Secrets Manager
pip install behave-data[all]     # Everything above
```

## Quickstart

Add this to `features/environment.py`:

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

Now your `.feature` files can use typed tables directly:

```gherkin
Feature: Typed users

  Scenario: Users with typed columns
    Given users
      | name:str | age:int | active:bool | created:date |
      | Alice    | 30      | true        | 2024-01-15   |
      | Bob      | 25      | false       | 2024-06-30   |
```

And in your steps:

```python
from behave import given
from behave_data import typed_wrap

@given("users")
def step_users(context):
    context.users = typed_wrap(context.table).typed_dicts()
```

`context.users[0]["age"]` is now an `int`, `active` a `bool`, `created` a `date`.

## Learn more

```{toctree}
:maxdepth: 2
:caption: Contents

quickstart
installation
typed_tables
null_handling
diff
raw_tables
dynamic_examples
fixtures
builders
secrets
tags
hooks
configuration
api
migration
changelog
```
