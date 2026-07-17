# Cookbook

Real-world recipes that combine behave-data features.

## Recipe: API test with fixtures, secrets, and diff

A complete example that sets up an API user from a fixture, loads an API token from an environment variable, and compares the response with an expected table.

### Project layout

```text
features/
  environment.py
  steps/
    api_steps.py
  api.feature
```

### environment.py

```python
from behave_data import (
    setup_data,
    before_feature_hook,
    before_scenario_hook,
    before_step_hook,
    after_scenario_hook,
    data_fixture,
)


@data_fixture("api_user")
def api_user():
    return {"name": "Alice", "role": "user"}


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

### api.feature

```gherkin
Feature: User API

  @needs_data:api_user
  Scenario: Get user profile
    Given the API token is "env:API_TOKEN"
    When I fetch the profile for user "api_user.name"
    Then the response matches
      | name:str | role:str |
      | Alice    | user     |
```

### api_steps.py

```python
import os
from behave import given, when, then
from behave_data import typed_wrap, diff


@given('the API token is "env:API_TOKEN"')
def step_token(context):
    context.token = context.data.resolve("env:API_TOKEN")


@when('I fetch the profile for user "api_user.name"')
def step_fetch(context):
    # In a real test you would call your API.
    # Here we simulate the response.
    context.response = {"name": "Alice", "role": "user"}


@then("the response matches")
def step_response_matches(context):
    diff(context.table, context.response)
```

## Recipe: Data-driven Scenario Outline from CSV

`features/data/users.csv`:

```text
name,email,age
alice,alice@example.com,30
bob,bob@example.com,25
```

`features/users.feature`:

```gherkin
Feature: User registration

  @load_examples:csv:features/data/users.csv
  Scenario Outline: Register user
    Given a user with name "<name>", email "<email>" and age <age>
    Then the user is valid

    Examples:
      | placeholder | placeholder | placeholder |
```

`features/steps/user_steps.py`:

```python
from behave import given, then


@given('a user with name "{name}", email "{email}" and age {age}')
def step_user(context, name, email, age):
    context.user = {"name": name, "email": email, "age": int(age)}


@then("the user is valid")
def step_valid(context):
    assert context.user["age"] > 0
    assert "@" in context.user["email"]
```

## Recipe: typed table with nullable dates

```gherkin
Feature: Events

  Scenario: List events
    Given events
      | name:str     | date:date?  |
      | Release      | 2024-07-15  |
      | Unscheduled  |             |
    Then 2 events exist
```

```python
from behave import given, then
from behave_data import typed_wrap


@given("events")
def step_events(context):
    context.events = typed_wrap(context.table).typed_dicts()


@then("{count:int} events exist")
def step_count(context, count):
    assert len(context.events) == count
    assert context.events[1]["date"] is None
```

## Recipe: reusable order builder

```python
from behave_data import data_builder


@data_builder("order")
def order(overrides):
    items = overrides.get("items", [])
    total = sum(item["price"] for item in items)
    return {
        "items": items,
        "total": total,
        **overrides,
    }
```

```python
order = context.data.build(
    "order",
    overrides={"items": [{"name": "Book", "price": 15}]},
)
# {"items": [{"name": "Book", "price": 15}], "total": 15}
```

## Recipe: cleanup with @cleanup_after

```gherkin
Feature: Cleanup demo

  @cleanup_after
  Scenario: Create record
    Given I create a record with name "temp"
    Then the record exists
```

```python
import os

records: list[str] = []


@given('I create a record with name "{name}"')
def step_create_record(context, name):
    records.append(name)

    def cleanup(_context):
        if name in records:
            records.remove(name)

    context._behave_data_cleanup_funcs.append(cleanup)


@then("the record exists")
def step_record_exists(context):
    assert records
```
