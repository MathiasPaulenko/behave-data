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

    def test_unknown_extension_returns_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "config.txt"
        path.write_text("some content", encoding="utf-8")
        cfg = Config.from_file(str(path))
        assert cfg == Config()

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

    def test_yaml_non_dict_returns_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "behave_data.yml"
        path.write_text("- just\n- a list\n", encoding="utf-8")
        cfg = Config.from_file(str(path))
        assert cfg == Config()

    def test_json_non_dict_returns_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "behave_data.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        cfg = Config.from_file(str(path))
        assert cfg == Config()


class TestFromUserdata:
    def test_empty_userdata_returns_defaults(self) -> None:
        cfg = Config.from_userdata({})
        assert cfg == Config()

    def test_null_markers_comma_separated(self) -> None:
        cfg = Config.from_userdata({"null_markers": ",null,None,N/A"})
        assert cfg.null_markers == frozenset({"", "null", "None", "N/A"})

    def test_secret_backend_string(self) -> None:
        cfg = Config.from_userdata({"secret_backend": "env"})
        assert cfg.secret_backend == "env"

    def test_secret_path_string(self) -> None:
        cfg = Config.from_userdata({"secret_path": "/tmp/secrets"})
        assert cfg.secret_path == "/tmp/secrets"

    def test_load_base_dir_string(self) -> None:
        cfg = Config.from_userdata({"load_base_dir": "data/"})
        assert cfg.load_base_dir == "data/"

    def test_null_markers_by_column_json(self) -> None:
        cfg = Config.from_userdata(
            {"null_markers_by_column": json.dumps({"phone": ["N/A", "null"]})}
        )
        assert cfg.null_markers_by_column["phone"] == frozenset({"N/A", "null"})

    def test_db_connections_json(self) -> None:
        cfg = Config.from_userdata(
            {"db_connections": json.dumps({"default": "sqlite:///test.db"})}
        )
        assert cfg.db_connections == {"default": "sqlite:///test.db"}

    def test_type_overrides_json(self) -> None:
        cfg = Config.from_userdata(
            {"type_overrides": json.dumps({"age": "int"})}
        )
        assert cfg.type_overrides == {"age": "int"}

    def test_invalid_json_skipped(self) -> None:
        cfg = Config.from_userdata(
            {"db_connections": "not json", "secret_backend": "env"}
        )
        assert cfg.db_connections == {}
        assert cfg.secret_backend == "env"

    def test_partial_userdata_merges_with_defaults(self) -> None:
        cfg = Config.from_userdata({"secret_backend": "env"})
        assert cfg.secret_backend == "env"
        assert cfg.null_markers == DEFAULT_NULL_MARKERS
        assert cfg.secret_path == "secrets/"

    def test_ignores_unknown_keys(self) -> None:
        cfg = Config.from_userdata({"unknown_key": "value", "secret_backend": "env"})
        assert cfg.secret_backend == "env"
        assert not hasattr(cfg, "unknown_key")
