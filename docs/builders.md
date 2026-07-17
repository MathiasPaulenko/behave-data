# Builders

Builders construct test data. Unlike fixtures, they are designed for derived fields and batch generation.

## Basic builder

```python
# features/environment.py
from behave_data import data_builder


@data_builder("product")
def product(overrides):
    return {
        "name": "Widget",
        "price": 9.99,
        **overrides,
    }
```

Use in a step:

```python
@when("I build a product")
def step_build_product(context):
    context.product = context.data.build("product")
```

Result:

```python
{"name": "Widget", "price": 9.99}
```

## With overrides

```python
product = context.data.build(
    "product",
    overrides={"name": "Gadget", "price": 19.99},
)
# {"name": "Gadget", "price": 19.99}
```

## Build multiple instances

```python
products = context.data.build("product", count=3)
# 3 products with default values
```

## Derived fields

Start from the overrides, apply defaults, then derive other fields:

```python
@data_builder("user")
def user(overrides):
    first_name = overrides.get("first_name", "Alice")
    last_name = overrides.get("last_name", "Smith")
    return {
        "first_name": first_name,
        "last_name": last_name,
        "full_name": f"{first_name} {last_name}",
        "role": overrides.get("role", "user"),
    }
```

Use it:

```python
user = context.data.build(
    "user",
    overrides={"first_name": "Bob", "role": "admin"},
)
# {"first_name": "Bob", "last_name": "Smith", "full_name": "Bob Smith", "role": "admin"}
```

## Manual registration

```python
from behave_data import DataManager

dm = DataManager()
dm.builders.register("order", lambda o: {"items": [], **o})
order = dm.build("order")
```

## Builder not found

```python
context.data.build("unknown")
# raises BuilderNotFoundError
```
