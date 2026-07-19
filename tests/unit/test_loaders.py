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

    def test_bom_handling(self, tmp_data_file: Path) -> None:
        """Regression: CSV files with UTF-8 BOM must not leak BOM into first header."""
        f = tmp_data_file / "bom.csv"
        f.write_bytes(b"\xef\xbb\xbfname,age\nAlice,30\n")
        result = CsvLoader().load(str(f), Config())
        assert len(result) == 1
        assert "name" in result[0]
        assert "\ufeffname" not in result[0]
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == "30"

    def test_extra_fields_stripped(self, tmp_data_file: Path) -> None:
        """Regression: CSV rows with more fields than headers must not produce None keys."""
        f = tmp_data_file / "ragged.csv"
        f.write_text("name,age\nAlice,30\nBob,25,extra\n", encoding="utf-8")
        result = CsvLoader().load(str(f), Config())
        assert len(result) == 2
        assert result[0] == {"name": "Alice", "age": "30"}
        assert result[1] == {"name": "Bob", "age": "25"}
        assert None not in result[1]


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

    def test_null_root_returns_empty_list(self, tmp_data_file: Path) -> None:
        """Regression: JSON file containing only null must not raise ValueError."""
        f = tmp_data_file / "null.json"
        f.write_text("null", encoding="utf-8")
        assert JsonLoader().load(str(f), Config()) == []

    def test_bom_handling(self, tmp_data_file: Path) -> None:
        """Regression: JSON files with UTF-8 BOM must parse correctly."""
        f = tmp_data_file / "bom.json"
        f.write_bytes(b"\xef\xbb\xbf" + json.dumps([{"name": "Alice"}]).encode("utf-8"))
        result = JsonLoader().load(str(f), Config())
        assert len(result) == 1
        assert result[0]["name"] == "Alice"


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

    def test_bom_handling(self, tmp_data_file: Path) -> None:
        """Regression: YAML files with UTF-8 BOM must parse correctly."""
        pytest.importorskip("yaml")
        from behave_data.loaders.yaml import YamlLoader

        f = tmp_data_file / "bom.yaml"
        f.write_bytes(b"\xef\xbb\xbf- name: Alice\n- name: Bob\n")
        result = YamlLoader().load(str(f), Config())
        assert len(result) == 2
        assert result[0]["name"] == "Alice"


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

    def test_no_active_worksheet(self, tmp_data_file: Path) -> None:
        from behave_data.loaders.excel import ExcelLoader

        mock_wb = MagicMock()
        mock_wb.active = None
        with patch.dict(
            sys.modules, {"openpyxl": MagicMock(load_workbook=lambda *a, **kw: mock_wb)}
        ):
            result = ExcelLoader().load("fake.xlsx", Config())
        assert result == []
        mock_wb.close.assert_called_once()

    def test_short_row_padded_with_none(self, tmp_data_file: Path) -> None:
        """Regression: rows with fewer cells than headers must be padded with None."""
        from behave_data.loaders.excel import ExcelLoader

        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            ("name", "age", "city"),
            ("Alice", 30),
        ]
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        with patch.dict(
            sys.modules, {"openpyxl": MagicMock(load_workbook=lambda *a, **kw: mock_wb)}
        ):
            result = ExcelLoader().load("fake.xlsx", Config())
        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == 30
        assert result[0]["city"] is None

    def test_extra_cells_get_col_n_keys(self, tmp_data_file: Path) -> None:
        """Regression: rows with more cells than headers get col_N keys."""
        from behave_data.loaders.excel import ExcelLoader

        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            ("name", "age"),
            ("Alice", 30, "extra"),
        ]
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        with patch.dict(
            sys.modules, {"openpyxl": MagicMock(load_workbook=lambda *a, **kw: mock_wb)}
        ):
            result = ExcelLoader().load("fake.xlsx", Config())
        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == 30
        assert result[0]["col_2"] == "extra"


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

    def test_query_with_db_name_prefix(self) -> None:
        from behave_data.loaders.sql import SqlLoader

        mock_result = MagicMock()
        mock_result.keys.return_value = ["name"]
        mock_result.__iter__ = lambda self: iter([("Alice",)])

        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = lambda self: self
        mock_conn.__exit__ = lambda self, *a: None

        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_conn

        mock_sa = MagicMock()
        mock_sa.create_engine.return_value = mock_engine
        mock_sa.text = lambda s: s

        config = Config(db_connections={"reporting": "sqlite:///report.db"})
        with patch.dict(sys.modules, {"sqlalchemy": mock_sa}):
            result = SqlLoader().load("reporting:SELECT name FROM users", config)

        assert result == [{"name": "Alice"}]
        mock_sa.create_engine.assert_called_once_with("sqlite:///report.db")
        mock_conn.execute.assert_called_once_with("SELECT name FROM users")

    def test_query_with_colon_uses_default_db(self) -> None:
        from behave_data.loaders.sql import SqlLoader

        mock_result = MagicMock()
        mock_result.keys.return_value = ["name"]
        mock_result.__iter__ = lambda self: iter([("Alice",)])

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
            SqlLoader().load("SELECT * FROM t WHERE x='a:b'", config)

        mock_sa.create_engine.assert_called_once_with("sqlite:///:memory:")
        mock_conn.execute.assert_called_once_with("SELECT * FROM t WHERE x='a:b'")

    def test_engine_disposed_after_query(self) -> None:
        """Regression: engine.dispose() must be called to release connection pool resources."""
        from behave_data.loaders.sql import SqlLoader

        mock_result = MagicMock()
        mock_result.keys.return_value = ["name"]
        mock_result.__iter__ = lambda self: iter([("Alice",)])

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
            SqlLoader().load("SELECT 1", config)

        mock_engine.dispose.assert_called_once()


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

    def test_method_without_url_raises(self) -> None:
        from behave_data.loaders.http import HttpLoader

        mock_requests = MagicMock()
        with (
            patch.dict(sys.modules, {"requests": mock_requests}),
            pytest.raises(ValueError, match="must include a URL"),
        ):
            HttpLoader().load("GET", Config())


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

    def test_relative_path_traversal_raises(self) -> None:
        config = Config(load_base_dir="features/data")
        with pytest.raises(ValueError, match="path traversal"):
            load("csv:../../etc/passwd", config)

    def test_relative_path_with_colon_rejected(self) -> None:
        """Regression: drive-relative colon paths must not bypass base validation."""
        config = Config(load_base_dir="features/data")
        with pytest.raises(ValueError, match="cannot contain ':'"):
            load("csv:C:../etc/passwd", config)

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

    def test_http_url_without_prefix(self) -> None:
        """Regression: load('http://...') must not strip the URL scheme."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "Alice"}]
        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        with patch.dict(sys.modules, {"requests": mock_requests}):
            result = load("http://api.example.com/users")
        assert result[0]["name"] == "Alice"
        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert call_args[0][0] == "http://api.example.com/users"

    def test_https_url_without_prefix(self) -> None:
        """Regression: load('https://...') must not strip the URL scheme."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "Bob"}]
        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        with patch.dict(sys.modules, {"requests": mock_requests}):
            result = load("https://api.example.com/users")
        assert result[0]["name"] == "Bob"
        call_args = mock_requests.get.call_args
        assert call_args[0][0] == "https://api.example.com/users"

    def test_http_prefix_with_url_still_works(self) -> None:
        """Regression: load('http:https://...') must pass the URL to HttpLoader."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "Carol"}]
        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        with patch.dict(sys.modules, {"requests": mock_requests}):
            result = load("http:https://api.example.com/users")
        assert result[0]["name"] == "Carol"
        call_args = mock_requests.get.call_args
        assert call_args[0][0] == "https://api.example.com/users"

    def test_get_method_prefix_detected(self) -> None:
        """Regression: load('GET https://...') must route to HttpLoader."""
        from behave_data.loaders import _detect_schema

        assert _detect_schema("GET https://api.example.com/users") == "https"
        assert _detect_schema("GET http://api.example.com/users") == "http"
        assert _detect_schema("get https://api.example.com/users") == "https"

    def test_post_method_prefix_detected(self) -> None:
        """Regression: load('POST https://...') must route to HttpLoader."""
        from behave_data.loaders import _detect_schema

        assert _detect_schema("POST https://api.example.com/users") == "https"
        assert _detect_schema("POST http://api.example.com/users") == "http"
        assert _detect_schema("post http://api.example.com/users") == "http"

    def test_get_method_prefix_load(self) -> None:
        """Regression: load('GET https://...') passes full source to HttpLoader."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "Dave"}]
        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        with patch.dict(sys.modules, {"requests": mock_requests}):
            result = load("GET https://api.example.com/users")
        assert result[0]["name"] == "Dave"
        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert call_args[0][0] == "https://api.example.com/users"

    def test_post_method_prefix_load(self) -> None:
        """Regression: load('POST https://...') passes full source to HttpLoader."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "Eve"}]
        mock_requests = MagicMock()
        mock_requests.post.return_value = mock_response

        with patch.dict(sys.modules, {"requests": mock_requests}):
            result = load("POST https://api.example.com/users")
        assert result[0]["name"] == "Eve"
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert call_args[0][0] == "https://api.example.com/users"

    def test_non_http_url_with_extension_not_detected_as_file(self) -> None:
        """Regression: URLs with non-HTTP schemes must not be detected by file extension."""
        from behave_data.loaders import _detect_schema

        assert _detect_schema("ftp://files.example.com/data.csv") is None
        assert _detect_schema("ftps://files.example.com/data.json") is None
        assert _detect_schema("sftp://files.example.com/data.yaml") is None
        assert _detect_schema("file:///C:/data/users.xlsx") is None
