# Typed Tables

behave-data extends [behave-tables](https://github.com/MathiasPaulenko/behave-tables) with automatic type conversion. Write your headers with type annotations and get native Python types in your steps.

## Basic syntax

```gherkin
| name:str | age:int | price:float | active:bool | created:date |
| Alice    | 30      | 9.99        | true        | 2024-01-15   |
| Bob      | 25      | 4.50        | false       | 2024-06-30   |
```

Supported types:

| Type | Example input | Python output |
|------|---------------|---------------|
| `str` | `hello` | `"hello"` |
| `int` | `42` | `42` |
| `float` | `3.14` | `3.14` |
| `bool` | `true` | `True` |
| `date` | `2024-01-15` | `datetime.date(2024, 1, 15)` |
| `datetime` | `2024-01-15T09:30:00` | `datetime.datetime(...)` |

## Using typed_wrap

```python
from behave_data import typed_wrap

@given("products")
def step_products(context):
    context.products = typed_wrap(context.table).typed_dicts()
```

`typed_dicts()` returns a list of dictionaries with converted values:

```python
[
    {"name": "Alice", "age": 30, "price": 9.99, "active": True, "created": date(2024, 1, 15)},
]
```

## Multiple rows

```python
context.products = typed_wrap(context.table).typed_dicts()
for product in context.products:
    assert product["price"] > 0
    assert isinstance(product["active"], bool)
```

## Nullable columns

Add `?` after the type to allow null values:

```gherkin
| name:str | age:int? | city:str? |
| Alice    | 30       | NYC       |
| Bob      | null     | N/A       |
| Carol    |          |           |
```

Result:

```python
[
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": None, "city": None},
    {"name": "Carol", "age": None, "city": None},
]
```

`age` and `city` are `None` for Bob and Carol because `"null"`, `"N/A"` and empty string are null markers.

## Typed objects

Convert to dataclasses or any class with `typed_objects()`:

```python
from dataclasses import dataclass

@dataclass
class Product:
    name: str
    price: float
    active: bool

context.products = typed_wrap(context.table).typed_objects(Product)
for product in context.products:
    assert product.price > 0
```

## Custom types

Register your own converter:

```python
from behave_data import register_type, typed_wrap

register_type("upper", lambda value: value.upper())
```

```gherkin
| code:upper |
| abc        |
```

Result: `{"code": "ABC"}`

## Headers without type

If no type is specified, the column is treated as `str`:

```gherkin
| name | age  |
| Alice| 30   |
```

Equivalently:

```gherkin
| name:str | age:str |
```

## Available methods

`typed_wrap(table)` returns a `TypedTableWrapper` with these methods:

- `typed_dicts()` — list of typed dicts
- `typed_objects(cls)` — list of typed objects
- `clean_headers()` — list of header names without type annotations
- plus all `behave-tables` methods: `as_dicts()`, `as_models()`, `transpose()`, `to_csv()`, etc.

## Handling conversion errors

Invalid values raise `TypeConversionError`:

```gherkin
| age:int |
| old     |
```

```python
from behave_data import TypeConversionError

try:
    typed_wrap(context.table).typed_dicts()
except TypeConversionError as exc:
    print(exc.column, exc.value, exc.type_name)
```
