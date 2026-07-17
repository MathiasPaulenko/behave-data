# Quickstart

This guide gets you from zero to typed tables in 5 minutes.

## 1. Install

```bash
pip install behave-data
```

For YAML support:

```bash
pip install behave-data[yaml]
```

## 2. Setup environment.py

Add to `features/environment.py`:

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

## 3. Write a feature with typed tables

Create `features/typed_users.feature`:

```gherkin
Feature: User management

  Scenario: Create users from typed table
    Given users
      | name:str | age:int | active:bool | created:date |
      | Alice    | 30      | true        | 2024-01-15   |
      | Bob      | 25      | false       | 2024-06-30   |
    Then all users are valid
```

## 4. Write the step definitions

Create `features/steps/user_steps.py`:

```python
from behave import given, then
from behave_data import typed_wrap


@given("users")
def step_users(context):
    context.users = typed_wrap(context.table).typed_dicts()


@then("all users are valid")
def step_all_users_valid(context):
    for user in context.users:
        assert isinstance(user["age"], int)
        assert isinstance(user["active"], bool)
        assert user["age"] > 0
```

## 5. Run

```bash
behave
```

Output:

```text
Feature: User management

  Scenario: Create users from typed table
    Given users
    Then all users are valid

1 feature passed, 0 failed, 0 skipped
1 scenario passed, 0 failed, 0 skipped
2 steps passed, 0 failed, 0 skipped
```

`context.users` will be:

```python
[
    {"name": "Alice", "age": 30, "active": True, "created": date(2024, 1, 15)},
    {"name": "Bob", "age": 25, "active": False, "created": date(2024, 6, 30)},
]
```

## Next steps

- Learn about [typed tables](typed_tables.md)
- Load [dynamic Examples](dynamic_examples.md)
- Create [fixtures](fixtures.md) and [builders](builders.md)
- Handle [secrets](secrets.md) safely
