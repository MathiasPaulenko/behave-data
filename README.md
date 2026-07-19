# behave-data

[![PyPI](https://img.shields.io/pypi/v/behave-data?label=PyPI)](https://pypi.org/project/behave-data/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://pypi.org/project/behave-data/)
[![Tests](https://img.shields.io/github/actions/workflow/status/MathiasPaulenko/behave-data/ci.yml?label=tests)](https://github.com/MathiasPaulenko/behave-data/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/github/actions/workflow/status/MathiasPaulenko/behave-data/docs.yml?label=docs&color=blueviolet)](https://mathiaspaulenko.github.io/behave-data/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/MathiasPaulenko/behave-data)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Data management for [Behave](https://github.com/behave/behave) — typed tables, diffs, dynamic examples, fixtures, and secrets with zero boilerplate.**

Built on top of [behave-tables](https://github.com/MathiasPaulenko/behave-tables).

> **Full documentation:** [mathiaspaulenko.github.io/behave-data](https://mathiaspaulenko.github.io/behave-data/)

## Quick links

- [Documentation](https://mathiaspaulenko.github.io/behave-data/)
- [Installation](https://mathiaspaulenko.github.io/behave-data/installation.html)
- [Quickstart](https://mathiaspaulenko.github.io/behave-data/quickstart.html)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [License](LICENSE)

---

## Why?

Behave data tables are strings. Everything is `"42"`, `"true"`, `""`. You write boilerplate in `environment.py` to convert types, handle nulls, load examples, and manage test data.

**behave-data** fixes this:

| Without behave-data | With behave-data |
| --- | --- |
| `row["age"]` → `"42"` (string) | `row["age"]` → `42` (int) |
| Empty cell → `""` | Empty cell → `None` |
| Hardcoded Examples in `.feature` | Load from CSV, JSON, YAML, Excel, SQL, HTTP |
| Manual `before_all` / `after_scenario` | `@needs_data`, `@with_fixture`, `@cleanup_after` tags |
| Secrets in feature files | `env:VAR`, `file:path`, `secret:name` with masking |

## Features

- **Typed Tables** — `name:str`, `age:int`, `active:bool`, `price:float`, `created:date` with automatic conversion
- **Null Resolution** — Empty cells become `None`, configurable markers (`""`, `"null"`, `"N/A"`), per-column overrides
- **Table Diff** — Cucumber-style diff output with row/column mismatch detection
- **Raw Tables** — Access tables without header assumption, vertical tables, transposed data
- **Dynamic Examples** — `@load_examples:csv:users.csv` replaces static Examples blocks
- **Fixtures** — Reusable data recipes with nesting (`ref:other`) and parametrization
- **Builders** — Construct test data with derived fields and overrides
- **Secrets** — `env:`, `file:`, `secret:` placeholders with Vault and AWS backends, automatic masking
- **Declarative Tags** — `@needs_data`, `@with_fixture`, `@cleanup_after` for zero-boilerplate setup/teardown

## Install

```bash
pip install behave-data
```

Optional extras:

| Extra | Packages | Use case |
| --- | --- | --- |
| `yaml` | PyYAML | YAML loader |
| `excel` | openpyxl | Excel loader |
| `sql` | SQLAlchemy | SQL loader |
| `http` | requests | HTTP loader |
| `vault` | hvac | HashiCorp Vault secrets |
| `aws` | boto3 | AWS Secrets Manager |
| `all` | all above | All optional loaders and backends |
| `dev` | pytest, ruff, mypy, build | Development |

```bash
pip install behave-data[yaml,excel]    # multiple extras
pip install behave-data[dev]           # contribute
```

## Quickstart

```python
# features/environment.py
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

```gherkin
# features/login.feature
@load_examples:csv:features/data/users.csv
Scenario Outline: User login
  Given a user with name "<name>" and email "<email>"
  When they log in
  Then they see the dashboard

  Examples:
```

```python
# features/steps/login.py
from behave_data import typed_wrap, diff

@then("the users should match")
def step_match(context):
    table = typed_wrap(context.table)
    for row in table.typed_dicts():
        assert isinstance(row["age"], int)      # typed, not string
        assert row["city"] is None or row["city"]  # None for empty cells
```

That's it. Type annotations in headers, nulls resolved, examples from external files, tags for setup/teardown — all automatic.

## Documentation

| Section | Link |
| --- | --- |
| Quickstart | [Quickstart](https://mathiaspaulenko.github.io/behave-data/quickstart.html) |
| Typed Tables | [Typed Tables](https://mathiaspaulenko.github.io/behave-data/typed_tables.html) |
| Null Handling | [Null Handling](https://mathiaspaulenko.github.io/behave-data/null_handling.html) |
| Table Diff | [Diff](https://mathiaspaulenko.github.io/behave-data/diff.html) |
| Dynamic Examples | [Dynamic Examples](https://mathiaspaulenko.github.io/behave-data/dynamic_examples.html) |
| Fixtures | [Fixtures](https://mathiaspaulenko.github.io/behave-data/fixtures.html) |
| Builders | [Builders](https://mathiaspaulenko.github.io/behave-data/builders.html) |
| Secrets | [Secrets](https://mathiaspaulenko.github.io/behave-data/secrets.html) |
| Declarative Tags | [Tags](https://mathiaspaulenko.github.io/behave-data/tags.html) |
| Hooks | [Hooks](https://mathiaspaulenko.github.io/behave-data/hooks.html) |
| Configuration | [Configuration](https://mathiaspaulenko.github.io/behave-data/configuration.html) |
| Cookbook | [Cookbook](https://mathiaspaulenko.github.io/behave-data/cookbook.html) |
| Troubleshooting | [Troubleshooting](https://mathiaspaulenko.github.io/behave-data/troubleshooting.html) |
| API Reference | [API](https://mathiaspaulenko.github.io/behave-data/api.html) |
| Migration Guide | [Migration](https://mathiaspaulenko.github.io/behave-data/migration.html) |
| Changelog | [Changelog](https://mathiaspaulenko.github.io/behave-data/changelog.html) |

## Migration from behave-tables

`behave-data` depends on `behave-tables` and extends it:

1. `pip install behave-data` — `behave-tables` comes as a dependency
2. Use `typed_wrap()` instead of `wrap()` for typed column conversion
3. Add `setup_data(context)` in `before_all()` to enable hooks, fixtures, builders, and secrets

All `behave-tables` APIs (`as_dicts`, `as_models`, `transpose`, `to_csv`, `to_json`, `find_row`, `select`, etc.) remain available via the re-exported `TableWrapper` and `wrap()`.

See the [Migration Guide](https://mathiaspaulenko.github.io/behave-data/migration.html) for details.

## Configuration

```yaml
# behave_data.yml
null_markers: ["", "null", "None", "N/A"]
null_markers_by_column:
  age: ["", "unknown"]
secret_backend: env
secret_path: secrets/
load_base_dir: features/data/
```

See [Configuration](https://mathiaspaulenko.github.io/behave-data/configuration.html) for all options.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for setup, development commands, and the release checklist.

For security issues, see [SECURITY.md](SECURITY.md).

## Acknowledgements

- Built on [behave-tables](https://github.com/MathiasPaulenko/behave-tables) for table manipulation.
- Inspired by the Behave community's need for first-class data handling in Gherkin scenarios.

## License

[MIT](LICENSE)
