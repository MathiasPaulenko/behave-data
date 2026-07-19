"""Tests for behave_data.config."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from behave_data.config import DEFAULT_NULL_MARKERS, Config
from behave_data.errors import OptionalDependencyError


class TestDefaults:
    def test_default_null_markers(self) -> None:
        cfg = Config()
        assert cfg.null_markers == DEFAULT_NULL_MARKERS

    def test_default_null_markers_by_column(self) -> None:
        cfg = Config()
        assert cfg.null_markers_by_column == {}

    def test_default_secret_backend(self) -> None:
        cfg = Config()
        assert cfg.secret_backend == "file"

    def test_default_secret_path(self) -> None:
        cfg = Config()
        assert cfg.secret_path == "secrets/"

    def test_default_load_base_dir(self) -> None:
        cfg = Config()
        assert cfg.load_base_dir == "features/data/"

    def test_default_db_connections(self) -> None:
        cfg = Config()
        assert cfg.db_connections == {}

    def test_default_type_overrides(self) -> None:
        cfg = Config()
        assert cfg.type_overrides == {}


class TestFromDict:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = Config.from_dict({})
        assert cfg == Config()

    def test_list_in_null_markers_converts_to_frozenset(self) -> None:
        cfg = Config.from_dict({"null_markers": ["", "NULL", "nil"]})
        assert isinstance(cfg.null_markers, frozenset)
        assert cfg.null_markers == frozenset({"", "NULL", "nil"})

    def test_list_in_null_markers_by_column_converts_to_frozenset(self) -> None:
        cfg = Config.from_dict({"null_markers_by_column": {"phone": ["N/A", "null"]}})
        assert isinstance(cfg.null_markers_by_column["phone"], frozenset)
        assert cfg.null_markers_by_column["phone"] == frozenset({"N/A", "null"})

    def test_ignores_unknown_keys(self) -> None:
        cfg = Config.from_dict({"unknown_key": "value", "secret_backend": "env"})
        assert cfg.secret_backend == "env"
        assert not hasattr(cfg, "unknown_key")

    def test_partial_data_merges_with_defaults(self) -> None:
        cfg = Config.from_dict({"secret_backend": "env"})
        assert cfg.secret_backend == "env"
        assert cfg.null_markers == DEFAULT_NULL_MARKERS
        assert cfg.secret_path == "secrets/"

    def test_frozenset_in_null_markers_stays_frozenset(self) -> None:
        cfg = Config.from_dict({"null_markers": frozenset({"a", "b"})})
        assert cfg.null_markers == frozenset({"a", "b"})

    def test_set_in_null_markers_converts_to_frozenset(self) -> None:
        cfg = Config.from_dict({"null_markers": {"a", "b"}})
        assert isinstance(cfg.null_markers, frozenset)
        assert cfg.null_markers == frozenset({"a", "b"})

    def test_frozenset_in_null_markers_by_column_stays_frozenset(self) -> None:
        cfg = Config.from_dict({"null_markers_by_column": {"phone": frozenset({"N/A", "null"})}})
        assert cfg.null_markers_by_column["phone"] == frozenset({"N/A", "null"})

    def test_set_in_null_markers_by_column_converts_to_frozenset(self) -> None:
        cfg = Config.from_dict({"null_markers_by_column": {"phone": {"N/A", "null"}}})
        assert isinstance(cfg.null_markers_by_column["phone"], frozenset)
        assert cfg.null_markers_by_column["phone"] == frozenset({"N/A", "null"})


class TestFromFile:
    def test_nonexistent_file_returns_defaults(self, tmp_path: Path) -> None:
        cfg = Config.from_file(str(tmp_path / "nonexistent.yml"))
        assert cfg == Config()

    def test_valid_yaml_file(self, tmp_path: Path) -> None:
        path = tmp_path / "behave_data.yml"
        path.write_text(
            "null_markers:\n"
            "  - ''\n"
            "  - null\n"
            "  - N/A\n"
            "secret_backend: env\n"
            "secret_path: /tmp/secrets\n",
            encoding="utf-8",
        )
        cfg = Config.from_file(str(path))
        assert cfg.secret_backend == "env"
        assert cfg.secret_path == "/tmp/secrets"
        assert cfg.null_markers == frozenset({"", "null", "N/A"})

    def test_valid_json_file(self, tmp_path: Path) -> None:
        path = tmp_path / "behave_data.json"
        path.write_text(
            json.dumps(
                {
                    "secret_backend": "env",
                    "load_base_dir": "data/",
                    "db_connections": {"test_db": "sqlite:///test.db"},
                }
            ),
            encoding="utf-8",
        )
        cfg = Config.from_file(str(path))
        assert cfg.secret_backend == "env"
        assert cfg.load_base_dir == "data/"
        assert cfg.db_connections == {"test_db": "sqlite:///test.db"}

    def test_unknown_extension_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.txt"
        path.write_text("some content", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported config file extension"):
            Config.from_file(str(path))

    def test_yaml_without_pyyaml_raises_optional_dependency_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "behave_data.yml"
        path.write_text("secret_backend: env\n", encoding="utf-8")

        monkeypatch.setitem(sys.modules, "yaml", None)
        with pytest.raises(OptionalDependencyError) as exc_info:
            Config.from_file(str(path))
        assert "pyyaml" in str(exc_info.value).lower()

    def test_yaml_file_with_list_in_null_markers_by_column(self, tmp_path: Path) -> None:
        path = tmp_path / "behave_data.yml"
        path.write_text(
            "null_markers_by_column:\n  phone:\n    - N/A\n    - null\n",
            encoding="utf-8",
        )
        cfg = Config.from_file(str(path))
        assert isinstance(cfg.null_markers_by_column["phone"], frozenset)
        assert cfg.null_markers_by_column["phone"] == frozenset({"N/A", "null"})

    def test_json_file_with_null_markers_list(self, tmp_path: Path) -> None:
        path = tmp_path / "behave_data.json"
        path.write_text(
            json.dumps({"null_markers": ["", "NULL"]}),
            encoding="utf-8",
        )
        cfg = Config.from_file(str(path))
        assert isinstance(cfg.null_markers, frozenset)
        assert cfg.null_markers == frozenset({"", "NULL"})

    def test_yaml_non_dict_raises(self, tmp_path: Path) -> None:
        """Regression: non-dict YAML must raise BehaveDataError, not return defaults."""
        from behave_data.errors import BehaveDataError

        path = tmp_path / "behave_data.yml"
        path.write_text("- just\n- a list\n", encoding="utf-8")
        with pytest.raises(BehaveDataError, match="must contain a mapping"):
            Config.from_file(str(path))

    def test_json_non_dict_raises(self, tmp_path: Path) -> None:
        """Regression: non-dict JSON must raise BehaveDataError, not return defaults."""
        from behave_data.errors import BehaveDataError

        path = tmp_path / "behave_data.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(BehaveDataError, match="must contain a mapping"):
            Config.from_file(str(path))

    def test_yaml_empty_file_raises(self, tmp_path: Path) -> None:
        """Regression: empty YAML file (None content) must raise BehaveDataError."""
        from behave_data.errors import BehaveDataError

        path = tmp_path / "behave_data.yml"
        path.write_text("", encoding="utf-8")
        with pytest.raises(BehaveDataError, match="must contain a mapping"):
            Config.from_file(str(path))

    def test_json_null_content_raises(self, tmp_path: Path) -> None:
        """Regression: JSON null content must raise BehaveDataError."""
        from behave_data.errors import BehaveDataError

        path = tmp_path / "behave_data.json"
        path.write_text("null", encoding="utf-8")
        with pytest.raises(BehaveDataError, match="must contain a mapping"):
            Config.from_file(str(path))


class TestFromUserdata:
    def test_empty_userdata_returns_defaults(self) -> None:
        cfg = Config.from_userdata({})
        assert cfg == Config()

    def test_null_markers_comma_separated(self) -> None:
        cfg = Config.from_userdata({"behave_data.null_markers": ",null,None,N/A"})
        assert cfg.null_markers == frozenset({"", "null", "None", "N/A"})

    def test_secret_backend_string(self) -> None:
        cfg = Config.from_userdata({"behave_data.secret_backend": "env"})
        assert cfg.secret_backend == "env"

    def test_secret_path_string(self) -> None:
        cfg = Config.from_userdata({"behave_data.secret_path": "/tmp/secrets"})
        assert cfg.secret_path == "/tmp/secrets"

    def test_load_base_dir_string(self) -> None:
        cfg = Config.from_userdata({"behave_data.load_base_dir": "data/"})
        assert cfg.load_base_dir == "data/"

    def test_null_markers_by_column_json(self) -> None:
        cfg = Config.from_userdata(
            {"behave_data.null_markers_by_column": json.dumps({"phone": ["N/A", "null"]})}
        )
        assert cfg.null_markers_by_column["phone"] == frozenset({"N/A", "null"})

    def test_db_connections_json(self) -> None:
        cfg = Config.from_userdata(
            {"behave_data.db_connections": json.dumps({"default": "sqlite:///test.db"})}
        )
        assert cfg.db_connections == {"default": "sqlite:///test.db"}

    def test_type_overrides_json(self) -> None:
        cfg = Config.from_userdata({"behave_data.type_overrides": json.dumps({"age": "int"})})
        assert cfg.type_overrides == {"age": "int"}

    def test_invalid_json_skipped(self) -> None:
        cfg = Config.from_userdata(
            {"behave_data.db_connections": "not json", "behave_data.secret_backend": "env"}
        )
        assert cfg.db_connections == {}
        assert cfg.secret_backend == "env"

    def test_partial_userdata_merges_with_defaults(self) -> None:
        cfg = Config.from_userdata({"behave_data.secret_backend": "env"})
        assert cfg.secret_backend == "env"
        assert cfg.null_markers == DEFAULT_NULL_MARKERS
        assert cfg.secret_path == "secrets/"

    def test_ignores_unprefixed_keys(self) -> None:
        cfg = Config.from_userdata({"secret_backend": "env", "behave_data.secret_backend": "file"})
        assert cfg.secret_backend == "file"

    def test_ignores_unknown_prefixed_keys(self) -> None:
        cfg = Config.from_userdata(
            {
                "behave_data.unknown_key": "value",
                "behave_data.secret_backend": "env",
            }
        )
        assert cfg.secret_backend == "env"
        assert not hasattr(cfg, "unknown_key")

    def test_mixed_prefixed_and_unprefixed(self) -> None:
        cfg = Config.from_userdata({"other_lib.foo": "bar", "behave_data.secret_backend": "env"})
        assert cfg.secret_backend == "env"
        assert not hasattr(cfg, "foo")


class TestFromDictEdgeCases:
    """Regression: from_dict must handle string, None, and invalid types for markers."""

    def test_null_markers_as_string_splits_by_comma(self) -> None:
        cfg = Config.from_dict({"null_markers": "null,None,N/A"})
        assert cfg.null_markers == frozenset({"null", "None", "N/A"})

    def test_null_markers_as_none_returns_empty_frozenset(self) -> None:
        cfg = Config.from_dict({"null_markers": None})
        assert cfg.null_markers == frozenset()

    def test_null_markers_as_int_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="must be a list or string"):
            Config.from_dict({"null_markers": 42})

    def test_null_markers_by_column_string_markers(self) -> None:
        cfg = Config.from_dict({"null_markers_by_column": {"phone": "N/A,null"}})
        assert cfg.null_markers_by_column["phone"] == frozenset({"N/A", "null"})

    def test_null_markers_by_column_none_markers(self) -> None:
        cfg = Config.from_dict({"null_markers_by_column": {"phone": None}})
        assert cfg.null_markers_by_column["phone"] == frozenset()

    def test_null_markers_by_column_invalid_type_raises(self) -> None:
        with pytest.raises(TypeError, match="must be a list or string"):
            Config.from_dict({"null_markers_by_column": {"phone": 42}})

    def test_null_markers_by_column_non_dict_raises_type_error(self) -> None:
        """Regression: from_dict with non-dict null_markers_by_column must raise TypeError."""
        with pytest.raises(TypeError, match="null_markers_by_column must be a dict"):
            Config.from_dict({"null_markers_by_column": "not a dict"})
        with pytest.raises(TypeError, match="null_markers_by_column must be a dict"):
            Config.from_dict({"null_markers_by_column": ["a", "b"]})
        with pytest.raises(TypeError, match="null_markers_by_column must be a dict"):
            Config.from_dict({"null_markers_by_column": 42})

    def test_from_userdata_invalid_json_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        cfg = Config.from_userdata({"behave_data.db_connections": "not valid json{"})
        assert cfg.db_connections == {}
        assert any("Invalid JSON" in r.message for r in caplog.records)

    def test_type_overrides_non_string_value_raises(self) -> None:
        with pytest.raises(TypeError, match="type_overrides\\['age'\\] must be a string"):
            Config.from_dict({"type_overrides": {"age": 123}})

    def test_db_connections_non_string_value_raises(self) -> None:
        with pytest.raises(TypeError, match="db_connections\\['default'\\] must be a string"):
            Config.from_dict({"db_connections": {"default": 123}})

    def test_db_connections_not_a_dict_raises(self) -> None:
        with pytest.raises(TypeError, match="db_connections must be a dict"):
            Config.from_dict({"db_connections": ["sqlite:///test.db"]})

    def test_type_overrides_not_a_dict_raises(self) -> None:
        with pytest.raises(TypeError, match="type_overrides must be a dict"):
            Config.from_dict({"type_overrides": ["int"]})

    def test_config_direct_invalid_type_overrides_raises(self) -> None:
        with pytest.raises(TypeError, match="type_overrides\\['age'\\] must be a string"):
            Config(type_overrides={"age": 123})

    def test_config_direct_null_markers_not_frozenset_raises(self) -> None:
        with pytest.raises(TypeError, match="null_markers must be a frozenset"):
            Config(null_markers=["null"])

    def test_config_direct_null_markers_by_column_not_dict_raises(self) -> None:
        with pytest.raises(TypeError, match="null_markers_by_column must be a dict"):
            Config(null_markers_by_column=["N/A"])

    def test_config_direct_null_markers_by_column_values_not_frozenset_raises(self) -> None:
        with pytest.raises(
            TypeError, match="null_markers_by_column\\['phone'\\] must be a frozenset"
        ):
            Config(null_markers_by_column={"phone": ["N/A"]})

    def test_config_direct_null_markers_elements_must_be_strings(self) -> None:
        with pytest.raises(TypeError, match="null_markers must contain only strings"):
            Config(null_markers=frozenset({1}))

    def test_config_direct_null_markers_by_column_elements_must_be_strings(self) -> None:
        with pytest.raises(
            TypeError, match="null_markers_by_column\\['phone'\\] must contain only strings"
        ):
            Config(null_markers_by_column={"phone": frozenset({1})})

    def test_from_dict_null_mapping_uses_defaults(self) -> None:
        cfg = Config.from_dict(
            {
                "db_connections": None,
                "type_overrides": None,
                "null_markers_by_column": None,
            }
        )
        assert cfg.db_connections == {}
        assert cfg.type_overrides == {}
        assert cfg.null_markers_by_column == {}

    def test_from_userdata_null_json_mapping_uses_defaults(self) -> None:
        import json

        cfg = Config.from_userdata(
            {
                "behave_data.db_connections": json.dumps(None),
                "behave_data.type_overrides": json.dumps(None),
            }
        )
        assert cfg.db_connections == {}
        assert cfg.type_overrides == {}

    def test_from_dict_null_string_fields_use_defaults(self) -> None:
        cfg = Config.from_dict(
            {
                "secret_backend": None,
                "secret_path": None,
                "load_base_dir": None,
            }
        )
        assert cfg.secret_backend == "file"
        assert cfg.secret_path == "secrets/"
        assert cfg.load_base_dir == "features/data/"

    # --- Regression tests for bug fixes ---

    def test_from_file_malformed_json_raises_behavedata_error(self, tmp_path: Path) -> None:
        """Regression: malformed JSON should raise BehaveDataError, not JSONDecodeError."""
        from behave_data.errors import BehaveDataError

        path = tmp_path / "bad.json"
        path.write_text("{invalid json}", encoding="utf-8")
        with pytest.raises(BehaveDataError, match="Malformed JSON"):
            Config.from_file(str(path))

    def test_from_file_malformed_yaml_raises_behavedata_error(self, tmp_path: Path) -> None:
        """Regression: malformed YAML should raise BehaveDataError, not YAMLError."""
        from behave_data.errors import BehaveDataError

        path = tmp_path / "bad.yml"
        path.write_text("key: [invalid\n  bad indent", encoding="utf-8")
        with pytest.raises(BehaveDataError, match="Malformed YAML"):
            Config.from_file(str(path))

    def test_config_secret_backend_must_be_str(self) -> None:
        """Regression: scalar fields must validate type."""
        with pytest.raises(TypeError, match="secret_backend must be a str"):
            Config(secret_backend=123)  # type: ignore[arg-type]

    def test_config_secret_path_must_be_str(self) -> None:
        with pytest.raises(TypeError, match="secret_path must be a str"):
            Config(secret_path=None)  # type: ignore[arg-type]

    def test_config_load_base_dir_must_be_str(self) -> None:
        with pytest.raises(TypeError, match="load_base_dir must be a str"):
            Config(load_base_dir=42)  # type: ignore[arg-type]

    def test_from_userdata_non_string_scalar_coerced(self) -> None:
        """Regression: non-string values in userdata should be coerced, not crash."""
        cfg = Config.from_userdata({"behave_data.secret_backend": 123})  # type: ignore[dict-item]
        assert cfg.secret_backend == "123"

    def test_from_userdata_non_string_null_markers_coerced(self) -> None:
        cfg = Config.from_userdata({"behave_data.null_markers": ",null,None"})  # type: ignore[dict-item]
        assert cfg.null_markers == frozenset({"", "null", "None"})

    def test_from_userdata_int_null_markers_coerced(self) -> None:
        """Regression: non-string null_markers value should be coerced to str."""
        cfg = Config.from_userdata({"behave_data.null_markers": 123})  # type: ignore[dict-item]
        assert cfg.null_markers == frozenset({"123"})
