"""Tests for behave_data.loaders."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from behave_data.config import Config
from behave_data.errors import LoaderNotFoundError, OptionalDependencyError
from behave_data.loaders import load
from behave_data.loaders.csv import CsvLoader
from behave_data.loaders.json import JsonLoader


@pytest.fixture
def tmp_data_file(tmp_path: Path) -> Path:
    """Create a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


class TestCsvLoader:
    def test_valid_csv(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "users.csv"
        f.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
        result = CsvLoader().load(str(f), Config())
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == "30"

    def test_nonexistent_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            CsvLoader().load("nonexistent.csv", Config())

    def test_empty_file(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "empty.csv"
        f.write_text("", encoding="utf-8")
        result = CsvLoader().load(str(f), Config())
        assert result == []

    def test_encoding(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "unicode.csv"
        f.write_text("name,city\nJos\xe9,M\xe9rida\n", encoding="utf-8")
        result = CsvLoader().load(str(f), Config())
        assert result[0]["name"] == "Jos\xe9"
        assert result[0]["city"] == "M\xe9rida"


class TestJsonLoader:
    def test_list(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "users.json"
        f.write_text(json.dumps([{"name": "Alice"}, {"name": "Bob"}]), encoding="utf-8")
        result = JsonLoader().load(str(f), Config())
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_dict(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "user.json"
        f.write_text(json.dumps({"name": "Alice"}), encoding="utf-8")
        result = JsonLoader().load(str(f), Config())
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_invalid_type_raises_value_error(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "bad.json"
        f.write_text("42", encoding="utf-8")
        with pytest.raises(ValueError):
            JsonLoader().load(str(f), Config())

    def test_malformed_json_raises(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "malformed.json"
        f.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            JsonLoader().load(str(f), Config())


class TestYamlLoader:
    def test_yaml_list(self, tmp_data_file: Path) -> None:
        pytest.importorskip("yaml")
        f = tmp_data_file / "users.yaml"
        f.write_text("- name: Alice\n- name: Bob\n", encoding="utf-8")
        from behave_data.loaders.yaml import YamlLoader

        result = YamlLoader().load(str(f), Config())
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_yaml_dict(self, tmp_data_file: Path) -> None:
        pytest.importorskip("yaml")
        f = tmp_data_file / "user.yaml"
        f.write_text("name: Alice\n", encoding="utf-8")
        from behave_data.loaders.yaml import YamlLoader

        result = YamlLoader().load(str(f), Config())
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_pyyaml_not_installed(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "users.yaml"
        f.write_text("- name: Alice\n", encoding="utf-8")
        from behave_data.loaders.yaml import YamlLoader

        with patch.dict(sys.modules, {"yaml": None}), pytest.raises(OptionalDependencyError):
            YamlLoader().load(str(f), Config())


class TestExcelLoader:
    def test_openpyxl_not_installed(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "users.xlsx"
        f.write_text("", encoding="utf-8")
        from behave_data.loaders.excel import ExcelLoader

        with patch.dict(sys.modules, {"openpyxl": None}), pytest.raises(OptionalDependencyError):
            ExcelLoader().load(str(f), Config())

    def test_valid_excel(self, tmp_data_file: Path) -> None:
        from behave_data.loaders.excel import ExcelLoader

        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            ("name", "age"),
            ("Alice", 30),
            ("Bob", 25),
        ]
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        with patch.dict(
            sys.modules, {"openpyxl": MagicMock(load_workbook=lambda *a, **kw: mock_wb)}
        ):
            result = ExcelLoader().load("fake.xlsx", Config())
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == 30

    def test_empty_excel(self, tmp_data_file: Path) -> None:
        from behave_data.loaders.excel import ExcelLoader

        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = []
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        with patch.dict(
            sys.modules, {"openpyxl": MagicMock(load_workbook=lambda *a, **kw: mock_wb)}
        ):
            result = ExcelLoader().load("fake.xlsx", Config())
        assert result == []


class TestSqlLoader:
    def test_sqlalchemy_not_installed(self) -> None:
        from behave_data.loaders.sql import SqlLoader

        with patch.dict(sys.modules, {"sqlalchemy": None}), pytest.raises(OptionalDependencyError):
            SqlLoader().load("SELECT 1", Config())

    def test_valid_query(self) -> None:
        from behave_data.loaders.sql import SqlLoader

        mock_result = MagicMock()
        mock_result.keys.return_value = ["name", "age"]
        mock_result.__iter__ = lambda self: iter([("Alice", 30), ("Bob", 25)])

        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = lambda self: self
        mock_conn.__exit__ = lambda self, *a: None

        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_conn

        mock_sa = MagicMock()
        mock_sa.create_engine.return_value = mock_engine
        mock_sa.text = lambda s: s

        config = Config(db_connections={"default": "sqlite:///:memory:"})
        with patch.dict(sys.modules, {"sqlalchemy": mock_sa}):
            result = SqlLoader().load("SELECT name, age FROM users", config)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == 30

    def test_db_not_found_in_config(self) -> None:
        from behave_data.loaders.sql import SqlLoader

        mock_sa = MagicMock()
        mock_sa.create_engine.return_value = MagicMock()
        mock_sa.text = lambda s: s
        config = Config(db_connections={})
        with patch.dict(sys.modules, {"sqlalchemy": mock_sa}), pytest.raises(KeyError):
            SqlLoader().load("SELECT 1", config)


class TestHttpLoader:
    def test_requests_not_installed(self) -> None:
        from behave_data.loaders.http import HttpLoader

        with patch.dict(sys.modules, {"requests": None}), pytest.raises(OptionalDependencyError):
            HttpLoader().load("GET https://api.example.com/users", Config())

    def test_valid_get_request(self) -> None:
        from behave_data.loaders.http import HttpLoader

        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "Alice"}, {"name": "Bob"}]
        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        with patch.dict(sys.modules, {"requests": mock_requests}):
            result = HttpLoader().load("GET https://api.example.com/users", Config())
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_valid_post_request(self) -> None:
        from behave_data.loaders.http import HttpLoader

        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "Alice"}]
        mock_requests = MagicMock()
        mock_requests.post.return_value = mock_response

        with patch.dict(sys.modules, {"requests": mock_requests}):
            result = HttpLoader().load("POST https://api.example.com/users", Config())
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_default_method_is_get(self) -> None:
        from behave_data.loaders.http import HttpLoader

        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "Alice"}]
        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        with patch.dict(sys.modules, {"requests": mock_requests}):
            result = HttpLoader().load("https://api.example.com/users", Config())
        assert result[0]["name"] == "Alice"

    def test_dict_response_wrapped(self) -> None:
        from behave_data.loaders.http import HttpLoader

        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "Alice"}
        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        with patch.dict(sys.modules, {"requests": mock_requests}):
            result = HttpLoader().load("GET https://api.example.com/user", Config())
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_unsupported_method_raises(self) -> None:
        from behave_data.loaders.http import HttpLoader

        mock_requests = MagicMock()
        with (
            patch.dict(sys.modules, {"requests": mock_requests}),
            pytest.raises(ValueError, match="Unsupported HTTP method"),
        ):
            HttpLoader().load("DELETE https://api.example.com/users", Config())


class TestLoadFunction:
    def test_schema_prefix_csv(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "users.csv"
        f.write_text("name,age\nAlice,30\n", encoding="utf-8")
        config = Config(load_base_dir=str(tmp_data_file))
        result = load(f"csv:{f.name}", config)
        assert result[0]["name"] == "Alice"

    def test_relative_path(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "users.csv"
        f.write_text("name,age\nAlice,30\n", encoding="utf-8")
        config = Config(load_base_dir=str(tmp_data_file))
        result = load("users.csv", config)
        assert result[0]["name"] == "Alice"

    def test_absolute_path(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "users.csv"
        f.write_text("name,age\nAlice,30\n", encoding="utf-8")
        result = load(str(f), Config())
        assert result[0]["name"] == "Alice"

    def test_unknown_extension_raises(self) -> None:
        with pytest.raises(LoaderNotFoundError):
            load("file.unknown", Config())

    def test_empty_file_returns_empty_list(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "empty.csv"
        f.write_text("", encoding="utf-8")
        result = load(str(f), Config())
        assert result == []

    def test_malformed_json_raises(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "bad.json"
        f.write_text("{not valid", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load(str(f), Config())

    def test_schema_prefix_json(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "users.json"
        f.write_text(json.dumps([{"name": "Alice"}]), encoding="utf-8")
        config = Config(load_base_dir=str(tmp_data_file))
        result = load(f"json:{f.name}", config)
        assert result[0]["name"] == "Alice"

    def test_no_config_uses_default(self, tmp_data_file: Path) -> None:
        f = tmp_data_file / "users.csv"
        f.write_text("name,age\nAlice,30\n", encoding="utf-8")
        result = load(str(f))
        assert result[0]["name"] == "Alice"
