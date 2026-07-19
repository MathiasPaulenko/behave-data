# Contributing to behave-data

Thank you for your interest in contributing! This document covers setup,
development commands, and the release process.

## Setup

```bash
git clone https://github.com/MathiasPaulenko/behave-data.git
cd behave-data
pip install -e ".[dev,all]"
pre-commit install
pre-commit run --all-files
```

## Development Commands

| Command | Description |
| :--- | :--- |
| `make dev` | Install with dev dependencies |
| `make lint` | Run ruff check |
| `make lint-fix` | Run ruff check with --fix |
| `make format` | Run ruff format |
| `make format-check` | Check formatting without changes |
| `make test` | Run pytest |
| `make test-cov` | Run pytest with coverage |
| `make build` | Build sdist + wheel |
| `make clean` | Remove build artifacts |

## Pre-PR Checklist

- [ ] `make lint` passes with 0 errors
- [ ] `make format-check` passes
- [ ] `make test-cov` passes with coverage >= 90%
- [ ] All public functions have type hints
- [ ] Tests cover happy path + edge cases
- [ ] Documentation updated if public APIs or behavior changed
- [ ] CHANGELOG.md updated (if user-facing changes)
- [ ] Backward compatibility considered

## Release Process

1. Ensure `CHANGELOG.md` has a section for the new version
2. Update `__version__` in `behave_data/__init__.py`
3. Update `version` in `pyproject.toml`
4. Run `make lint`, `make format-check`, and `make test-cov`
5. Commit: `git commit -m "release: vX.Y.Z"`
6. Tag: `git tag vX.Y.Z`
7. Push the commit and tag: `git push && git push --tags`
8. CI builds, publishes to PyPI, and creates a GitHub Release
