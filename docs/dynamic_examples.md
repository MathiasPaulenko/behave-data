# Dynamic Examples

Replace static `Examples` blocks with data from CSV, JSON, YAML, Excel, SQL, or HTTP APIs.

## Basic syntax

Tag a `Scenario Outline` with `@load_examples:<source>`. You still need an `Examples:` block; behave-data replaces its rows at runtime.

```gherkin
@load_examples:csv:users.csv
Scenario Outline: Create user
  Given I have a user with name "<name>" and email "<email>"
  Then the user is valid

  Examples:
    | placeholder | placeholder |
```

Relative paths are resolved against `load_base_dir` (`features/data/` by default).

### Tag limitations

Behave strips `/`, `\`, and whitespace from tag names, and splits tags on
spaces. A tag can therefore only carry sources without those characters —
basically `csv:users.csv`-style paths relative to `load_base_dir`.

For anything else (nested paths, URLs, SQL queries), register the source
in `data_sources` and reference it by name:

```yaml
# behave_data.yml
data_sources:
  users_from_api: "http:https://api.example.com/users"
  users_query: "sql:SELECT name, email FROM users"
  users_csv: "csv:features/data/users.csv"
```

```gherkin
@load_examples:users_from_api
Scenario Outline: Create user
  ...
```

## CSV file

`features/data/users.csv`:

```text
name,email
alice,alice@example.com
bob,bob@example.com
carol,carol@example.com
```

Result: the scenario runs 3 times, once per row, with `<name>` and `<email>` replaced.

## JSON file

`features/data/users.json`:

```json
[
  {"name": "alice", "email": "alice@example.com"},
  {"name": "bob", "email": "bob@example.com"}
]
```

Feature:

```gherkin
@load_examples:json:users.json
Scenario Outline: Create user
  Given I have a user with name "<name>" and email "<email>"

  Examples:
    | placeholder | placeholder |
```

## YAML file

`features/data/users.yaml`:

```yaml
- name: alice
  email: alice@example.com
- name: bob
  email: bob@example.com
```

Feature:

```gherkin
@load_examples:yaml:users.yaml
Scenario Outline: Create user

  Examples:
    | placeholder | placeholder |
```

Requires `pip install behave-data[yaml]`.

## Excel file

```gherkin
@load_examples:excel:users.xlsx
Scenario Outline: Create user

  Examples:
    | placeholder | placeholder |
```

Requires `pip install behave-data[excel]`.

## SQL query

SQL queries contain spaces and can't appear in a tag — use `data_sources`:

```yaml
data_sources:
  all_users: "sql:SELECT name, email FROM users"
```

```gherkin
@load_examples:all_users
Scenario Outline: Create user

  Examples:
    | placeholder | placeholder |
```

Requires `pip install behave-data[sql]` and a configured connection.

## HTTP endpoint

URLs contain `/`, so they also go through `data_sources`:

```yaml
data_sources:
  users_api: "http:https://api.example.com/users"
```

```gherkin
@load_examples:users_api
Scenario Outline: Create user

  Examples:
    | placeholder | placeholder |
```

Requires `pip install behave-data[http]`.

## Per-Examples-block tags

A Scenario Outline can have several `Examples` blocks. A tag on a block
applies only to that block and overrides the scenario-level tag:

```gherkin
Scenario Outline: Create user
  Given I have a user with name "<name>" and email "<email>"

  @load_examples:csv:admins.csv
  Examples: admins
    | placeholder | placeholder |

  @load_examples:csv:users.csv
  Examples: regular users
    | placeholder | placeholder |
```

## Configuration

Set the base directory for relative paths in `behave_data.yml`:

```yaml
load_base_dir: features/data/
```

Then use:

```gherkin
@load_examples:csv:users.csv
```

## Supported formats

| Schema      | Description             | Extra     |
|-------------|-------------------------|-----------|
| `csv:`      | Comma-separated values  | —         |
| `json:`     | JSON array of objects   | —         |
| `yaml:`     | YAML list or dict       | `[yaml]`  |
| `excel:`    | Excel `.xlsx` file      | `[excel]` |
| `xlsx:`     | Alias for `excel:`      | `[excel]` |
| `sql:`      | SQL SELECT query        | `[sql]`   |
| `http:`     | HTTP GET returning JSON | `[http]`  |

## How it works

`before_feature_hook` scans every `Scenario Outline` for `@load_examples:` tags. When found, it loads the data and replaces the rows inside the `Examples` block before the outline runs.
