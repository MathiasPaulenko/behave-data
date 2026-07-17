# Migration Guide

## From raw Behave tables

Before:

```python
@given("products")
def step_products(context):
    products = []
    for row in context.table:
        products.append({
            "name": row["name"],
            "price": float(row["price"]),
            "active": row["active"] == "true",
        })
    context.products = products
```

After:

```python
from behave_data import typed_wrap

@given("products")
def step_products(context):
    context.products = typed_wrap(context.table).typed_dicts()
```

Feature:

```gherkin
| name:str | price:float | active:bool |
| Widget   | 9.99        | true        |
```

## From behave-tables

behave-data builds on `behave-tables`. You can keep using `TableWrapper` methods:

```python
from behave_data import typed_wrap

wrapper = typed_wrap(context.table)
context.dicts = wrapper.as_dicts()  # from behave-tables
context.typed = wrapper.typed_dicts()  # from behave-data
```

## From static Examples

Before:

```gherkin
Scenario Outline: Create user
  Given I create user "<name>" with email "<email>"

  Examples:
    | name  | email               |
    | alice | alice@example.com   |
    | bob   | bob@example.com     |
```

After:

```gherkin
@load_examples:csv:features/data/users.csv
Scenario Outline: Create user
  Given I create user "<name>" with email "<email>"

  Examples:
    | placeholder | placeholder |
```

## Fixtures vs plain dicts

Before:

```python
def before_scenario(context, scenario):
    context.user = {"name": "Alice", "role": "user"}
```

After:

```python
from behave_data import data_fixture

@data_fixture("user")
def user():
    return {"name": "Alice", "role": "user"}
```

```gherkin
@needs_data:user
Scenario: Alice logs in
```

## Secrets in feature files

Before:

```gherkin
| name | token       |
| Alice| supersecret |
```

After:

```gherkin
| name  | token           |
| Alice | secret:API_TOKEN |
```

And in step:

```python
token = context.data.resolve(context.user["token"])
```
