# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-07-17

### Added

- Sphinx documentation site with furo theme
- 13 documentation pages: quickstart, installation, typed tables, null handling, diff, raw tables, dynamic examples, fixtures, builders, secrets, tags, hooks, configuration, API reference, migration guide, changelog
- GitHub Actions workflow `docs.yml` to build and deploy docs to GitHub Pages
- Documentation URL in `pyproject.toml`
- `docs` and `all` optional dependency extras

### Fixed

- `test_to_pandas_raises_without_pandas` now uses `monkeypatch` on `sys.modules["pandas"]` for robustness when `pandas` extra is installed

## [0.1.3] - 2026-07-17

### Added

- 75 edge case unit tests covering hooks, secrets, examples, raw_table, yaml, types, diff, fixtures, loaders, config, and manager
- 4 new E2E Behave integration features: fixtures_builders, secrets, typed_table_edge, dynamic_examples
- 27 E2E scenarios with 64 steps testing all behave-data features in real Behave

### Fixed

- `tags.py` now strips `@` prefix from Behave tags (Behave strips `@` from scenario tags)
- `tags.py` `@needs_data` now sets attribute on context in addition to `_behave_data_loaded`
- `tags.py` cleanup functions now support both `func(context)` and `func()` signatures

### Changed

- Coverage increased from 94% to 98%
- Total tests: 411 passed, 1 skipped (pandas optional)

## [0.1.2] - 2026-07-17

### Fixed

- `mypy --strict` passes with zero errors
- Added `[tool.mypy]` config with `ignore_missing_imports = true`
- Fixed `RawTable.__hash__` type signature
- Fixed `secrets.py` vault/aws return type annotations
- Fixed `loaders/__init__.py` loader return type annotation
- Fixed `examples.py` `_SimpleRow._headers` attribute
- Removed unused `type: ignore` comments in `patch.py` and `raw_table.py`

## [0.1.1] - 2026-07-17

### Added

- Fixtures registry with scoping, nesting (`ref:`), and parametrization (`@data_fixture`)
- Builders registry with derived fields, overrides, and count support (`@data_builder`)
- Full `DataManager` — unified access to fixtures, builders, and secret resolution
- Secret masking — values resolved via `secret:` are automatically masked with `***`
- Advanced secret backends: `env`, `vault` (HashiCorp Vault via hvac), `aws` (AWS Secrets Manager via boto3)
- Declarative tags: `@needs_data:name`, `@with_fixture:name`, `@cleanup_after`
- `before_feature_hook` — loads dynamic Examples before a feature runs
- `before_scenario_hook` / `after_scenario_hook` — tag processing and cleanup
- `process_tags_before_scenario` / `process_tags_after_scenario` — tag processing functions
- Comprehensive README with full API reference, examples, and migration guide

### Changed

- `DataManager` is no longer a stub — full implementation with `fixture()`, `build()`, `resolve()`, `mask()`
- `resolve_placeholder` now supports `secret:` prefix with configurable backends
- `setup_data` now accepts `Config | None` (defaults to `Config()`)

## [0.1.0] - 2026-07-17

### Added

- Core types: `int`, `float`, `bool`, `str`, `date`, `datetime` with `register_type()` and `convert_cell()`
- Null resolution: configurable null markers, per-column overrides, `is_null()`, `resolve_null()`
- `TypedTableWrapper` with `typed_dicts()` and `typed_objects()`
- `RawTable` for headerless table access
- Table diff with Cucumber-style output and `TableDiffError`
- `Config` dataclass with `from_file()` for `behave_data.yml`
- Behave patches: `apply_patches()` / `revert_patches()`
- Data loaders: CSV, JSON, YAML, Excel, SQL, HTTP with lazy imports
- Dynamic Examples loading via `@load_examples:source` tags
- Secret placeholders: `env:VAR`, `file:path`, `ref:fixture`
- `setup_data()` and `before_step_hook()` for Behave integration
- `DataManager` stub (full implementation in 0.1.1)
- Project scaffolding: CI/CD, community files, Makefile, pre-commit
