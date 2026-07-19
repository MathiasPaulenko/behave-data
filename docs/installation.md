# Installation

## Requirements

- Python 3.11+
- `behave` 1.2.6+
- `behave-tables` 1.3.0+

## Basic install

```bash
pip install behave-data
```

## Optional extras

| Extra    | Description         | Installs                                        |
|----------|---------------------|-------------------------------------------------|
| `yaml`   | YAML loader         | `pyyaml`                                        |
| `excel`  | Excel loader        | `openpyxl`                                      |
| `sql`    | SQL loader          | `sqlalchemy`                                    |
| `http`   | HTTP loader         | `requests`                                      |
| `pandas` | Pandas conversion   | `pandas`                                        |
| `vault`  | Vault secrets       | `hvac`                                          |
| `aws`    | AWS Secrets Manager | `boto3`                                         |
| `dev`    | Test/lint tools     | `pytest`, `pytest-cov`, `ruff`, `mypy`, `build` |
| `docs`   | Documentation tools | `sphinx`, `furo`, `myst-parser`                 |
| `all`    | All optional deps   | All of the above                                |

Install with extras:

```bash
pip install behave-data[yaml,excel,http]
pip install behave-data[all]
pip install behave-data[dev,yaml,docs]  # For contributors
```

## Verify installation

```python
import behave_data
print(behave_data.__version__)
```

To run the test suite after cloning the repository:

```bash
git clone https://github.com/MathiasPaulenko/behave-data.git
cd behave-data
pip install -e ".[dev,all]"
make test-cov
```

## From source

```bash
git clone https://github.com/MathiasPaulenko/behave-data.git
cd behave-data
pip install -e ".[dev,all]"
```
