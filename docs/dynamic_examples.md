# Dynamic Examples

Replace static `Examples` blocks with data from CSV, JSON, YAML, Excel, SQL, or HTTP APIs.

## Basic syntax

Use the `@load_examples:` tag on a `Scenario Outline`:

```gherkin
@load_examples:csv:features/data/users.csv
Scenario Outline: Create user
  Given I have a user with name "<name>" and email "<email>"
  Then the user is valid

  Examples:
    | placeholder | placeholder |
```

The static `Examples` block is replaced at runtime by the CSV content.

## CSV file

`features/data/users.csv`:

```text
name,email
alice,alice@example.com
bob,bob@example.com
carol,carol@example.com
```

Result: the scenario runs 3 times, once per row.

## JSON file

```gherkin
@load_examples:json:features/data/users.json
Scenario Outline: Create user
```

`features/data/users.json`:

```json
[
  {"name": "alice", "email": "alice@example.com"},
  {"name": "bob", "email": "bob@example.com"}
]
```

## YAML file

```gherkin
@load_examples:yaml:features/data/users.yaml
Scenario Outline: Create user
```

Requires `pip install behave-data[yaml]`.

## Excel file

```gherkin
@load_examples:excel:features/data/users.xlsx
Scenario Outline: Create user
```

Requires `pip install behave-data[excel]`.

## SQL query

```gherkin
@load_examples:sql:SELECT name, email FROM users
Scenario Outline: Create user
```

Requires `pip install behave-data[sql]` and a configured connection.

## HTTP endpoint

```gherkin
@load_examples:http:https://api.example.com/users
Scenario Outline: Create user
```

Requires `pip install behave-data[http]`.

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

| Schema   | Description               | Extra    |
|----------|---------------------------|----------|
| `csv:`   | Comma-separated values    | —        |
| `json:`  | JSON array of objects     | —        |
| `yaml:`  | YAML list or dict         | `[yaml]` |
| `excel:` | Excel `.xlsx` file        | `[excel]` |
| `sql:`   | SQL SELECT query          | `[sql]`  |
| `http:`  | HTTP GET returning JSON   | `[http]` |

## How it works

`before_feature_hook` scans the feature for `@load_examples:` tags. When found, it loads the data and replaces the `Examples` table rows before the scenario outline runs.
