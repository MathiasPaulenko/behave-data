# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
