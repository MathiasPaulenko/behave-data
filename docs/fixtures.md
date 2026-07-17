# Fixtures

Fixtures are reusable data recipes. Register them once, use them everywhere.

## Basic fixture

Register fixtures in `features/environment.py` (or any module imported before `setup_data` runs):

```python
# features/environment.py
from behave_data import data_fixture


@data_fixture("admin_user")
def admin_user():
    return {
        "name": "Admin User",
        "role": "admin",
        "email": "admin@example.com",
    }
```

Use in a feature:

```gherkin
@needs_data:admin_user
Scenario: Admin can access dashboard
  Given I am logged in as admin
  Then I see the admin dashboard
```

In the step:

```python
from behave import given, then

@given("I am logged in as admin")
def step_admin_login(context):
    user = context.admin_user
    assert user["role"] == "admin"


@then("I see the admin dashboard")
def step_see_dashboard(context):
    assert context.admin_user["role"] == "admin"
```

You can also retrieve the fixture manually:

```python
user = context.data.fixture("admin_user")
```

## Manual registration

```python
from behave_data import DataManager

dm = DataManager()
dm.fixtures.register("guest", lambda: {"name": "Guest", "role": "guest"})
user = dm.fixture("guest")
```

## Nested fixtures with ref

Reference another fixture inside a fixture using `ref:<name>`:

```python
@data_fixture("address")
def address():
    return {"street": "123 Main St", "city": "NYC"}


@data_fixture("user_with_address")
def user_with_address():
    return {
        "name": "Alice",
        "address": "ref:address",
    }
```

Retrieve it:

```python
user = context.data.fixture("user_with_address")
assert user == {
    "name": "Alice",
    "address": {"street": "123 Main St", "city": "NYC"},
}
```

## Parametrized fixtures

```python
@data_fixture("regular_user", params=["alice", "bob"])
def regular_user(name):
    return {"name": name, "role": "user"}
```

Each parameter is registered as a separate fixture name: `regular_user:alice`, `regular_user:bob`.

Use it in a feature:

```gherkin
@needs_data:regular_user:alice
Scenario: Alice logs in
  Given I am logged in
  Then my name is "alice"
```

In the step:

```python
@then('my name is "alice"')
def step_name_is_alice(context):
    assert context.regular_user_alice["name"] == "alice"
```

Or retrieve manually:

```python
user = context.data.fixture("regular_user:alice")
```

## Fixture overrides

Override fields when retrieving:

```python
user = context.data.fixture("admin_user", email="custom@example.com")
# {"name": "Admin User", "role": "admin", "email": "custom@example.com"}
```

## Circular reference detection

Self-references raise an error:

```python
@data_fixture("loop")
def loop():
    return {"self": "ref:loop"}

# raises BehaveDataError: Circular fixture reference
```

## Scope

You can specify scope (ignored by current implementation, reserved for future):

```python
@data_fixture("config", scope="feature")
def config():
    return {"timeout": 30}
```

## With DataManager

```python
from behave_data import DataManager

dm = DataManager()
dm.fixtures.register("item", lambda: {"name": "Book", "price": 10})
item = dm.fixture("item")
```
