# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-10-02

### Added

- `data_sources` config option: named sources for `@load_examples:<name>` tags and `load(<name>)` calls. Required for sources Behave's tag sanitizer can't carry (paths with `/`, URLs, SQL queries).
- `@load_examples:` tags can now be placed on an individual `Examples:` block, overriding the scenario/feature tag for that block.
- `context.resolved_text`: doc strings are placeholder-resolved alongside `context.resolved_table`.
- `{placeholder}` resolution supports dict key access (`{user.email}` works when `context.user` is a dict).
- `diff()` accepts `list[dict]` and `dict` for the `expected` argument too.
- `Config` is now hashable.
- Re-registering a builder/fixture name logs a warning.

### Fixed

- **`@load_examples` never matched**: the tag pattern required a leading `@`, but Behave delivers `scenario.tags`/`feature.tags` without it. The feature now works; integration tests assert real loaded data.
- `before_step_hook` leaked the previous step's `resolved_table` into steps without a table; both `resolved_table` and `resolved_text` are now reset to `None`.
- A non-callable entry in `_behave_data_cleanup_funcs` aborted all subsequent cleanups; it's now collected like other cleanup errors.
- `diff()` silently ignored dict keys that appeared only in later `actual` rows; headers are now the union of all row keys.
- `@needs_data:`/`@with_fixture:` with parametrized names (`user:alice`) created unusable `context."user:alice"` attributes; the base name is set instead, and reserved names (`data`, `config`, ...) are skipped.
- `RawTable` rendered `None` cell values as the literal string `"None"`; they now become `""`.
- `is_null`/`resolve_null` raised `TypeError` on unhashable values (lists, dicts).
- `Config.from_dict` silently dropped unknown keys; it now logs a warning.
- `DataManager.mask()` only masked exact matches; secrets embedded in larger strings are now replaced too.
- `BuilderRegistry`/`FixtureRegistry` snapshots missed builders/fixtures registered after instantiation; lookups now fall back to the global registries.
- `revert_patches()` deleted attributes that other code had replaced after `apply_patches()`; it now only restores/removes attributes that are still ours.
- `setup_data()` only tried `behave_data.yml`; it now picks the first existing of `.yml`/`.yaml`/`.json`.

### Changed

- **Minimum behave version is now 1.3.0** (was 1.2.6). On behave 1.2.x, `Context.__getattr__` raises `KeyError` (not `AttributeError`) for missing `_`-prefixed attributes, which crashed `before_scenario`/`after_scenario` hooks on `hasattr`/`getattr` defaults. Rather than carry compat shims, the floor was raised to the current stable line.
- CI now runs the test matrix against behave 1.3.0 and latest.

### Docs

- `hooks.md` no longer claims step-text placeholders are resolved before matching (impossible — matching happens first); documents `resolved_table`/`resolved_text` and dict access.
- `dynamic_examples.md` documents tag character limitations and `data_sources`; all path examples use `load_base_dir`-relative names.

## [1.0.2] - 2026-07-19

### Fixed

- Move empty-source validation before `import requests` in `HttpLoader.load()` so `ValueError` is raised regardless of whether `requests` is installed.
- Add `http` extra to CI dependencies so HTTP loader tests can run with `requests` installed.

## [1.0.1] - 2026-07-19

### Fixed

- Fixed mypy cross-version compatibility: removed `--strict` flag from CI command (already in `pyproject.toml`), allowing `warn_unused_ignores = false` to take effect across Python 3.11–3.14.
- Removed redundant `cast()` in `TypedTableWrapper.headings` property.

## [1.0.0] - 2026-07-19

First stable release. The API is frozen and ready for production use.

### Added

- `excel` schema alias for `@load_examples` tags (in addition to `xlsx`).
- `wrap` and `TableWrapper` re-exports documented in the API reference.
- `docs/migration.md` — step-by-step migration guide from behave-tables.
- `MANIFEST.in` to ensure LICENSE and README are included in the sdist.
- `pre-commit` to the `dev` extras.
- Regression tests for `TableLike` compatibility, `resolve_placeholder` type checking, and `Config` marker validation.

### Fixed

- `TypedTableWrapper` now fully satisfies the `TableLike` protocol, exposing `headings` and `rows` properties.
- `TypedTableWrapper` can re-wrap an existing `TableWrapper` or `TypedTableWrapper` without re-extracting rows.
- `resolve_placeholder` raises a clear `TypeError` when given a non-string value.
- `Config` validates that `null_markers` and `null_markers_by_column` contain only string values.
- Codecov action updated to v4 with token authentication in CI.

### Changed

- Version bumped to 1.0.0 — API is considered stable.
- `Development Status` classifier set to `Production/Stable`.
- Coverage threshold enforced at 90% in `Makefile` and `pyproject.toml`.
- Polished README, documentation, contributing guidelines, security policy, and package metadata for public release.
- Improved `TypedTableWrapper.typed_dicts()` performance by precomputing column type and null-marker metadata once per call.

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
