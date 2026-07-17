# Declarative Tags

behave-data provides tags that reduce boilerplate in `environment.py`.

## @needs_data

Load a fixture into the context before the scenario runs.

```gherkin
@needs_data:admin_user
Scenario: Admin can see dashboard
  Given I am logged in
  Then I see the admin dashboard
```

In `environment.py`:

```python
from behave_data import data_fixture


@data_fixture("admin_user")
def admin_user():
    return {"name": "Admin", "role": "admin"}
```

In the step:

```python
@given("I am logged in")
def step_logged_in(context):
    user = context.admin_user
    assert user["role"] == "admin"
```

## @with_fixture

Like `@needs_data`, but explicitly assigns the fixture to `context.<name>`:

```gherkin
@with_fixture:admin_user
Scenario: Admin logs in
```

## @needs_data with parametrized fixture

```gherkin
@needs_data:regular_user:alice
Scenario: Alice logs in
```

## @cleanup_after

Mark a scenario for cleanup after it runs:

```gherkin
@cleanup_after
Feature: Temporary files

  Scenario: Create and clean temporary file
    Given I create a temp file
    Then the temp file exists
```

Register cleanup inside a step:

```python
import os
import tempfile

from behave import given, then


@given("I create a temp file")
def step_create_temp(context):
    context.temp_file = tempfile.NamedTemporaryFile(delete=False)

    def cleanup(c):
        c.temp_file.close()
        os.unlink(c.temp_file.name)

    context._behave_data_cleanup_funcs.append(cleanup)


@then("the temp file exists")
def step_temp_exists(context):
    assert os.path.exists(context.temp_file.name)
```

`after_scenario_hook` runs every function in `context._behave_data_cleanup_funcs`, even if the scenario fails. Functions can take `context` or no arguments.

## Feature-level tags

Tags at feature level are also processed:

```gherkin
@needs_data:config
Feature: All scenarios need config

  Scenario: One
  Scenario: Two
```

## Combination

```gherkin
@needs_data:admin_user
@cleanup_after
Scenario: Admin creates and removes record
```

## Custom tag processing

You can also process tags manually:

```python
from behave_data.tags import process_tags_before_scenario

process_tags_before_scenario(context, scenario)
```
