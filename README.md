# behave-data

Data management for Behave — typed tables, diff, dynamic examples, fixtures, secrets.

## Install

```bash
pip install behave-data
```

For development:

```bash
pip install -e ".[dev,yaml,excel]"
```

## Quickstart

```python
# features/environment.py
from behave_data import setup_data, before_step_hook

def before_all(context):
    setup_data(context)

def before_step(context, step):
    before_step_hook(context, step)
```

```python
# features/steps/typing.py
from behave_data import typed_wrap

@then("the car should have")
def step_car(context):
    table = typed_wrap(context.table)
    cars = table.typed_objects(Car)
    for car in cars:
        assert car.doors == 4  # int, not str
```

## License

MIT
