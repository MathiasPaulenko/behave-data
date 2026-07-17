"""Tests for behave_data.secrets."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from behave_data.config import Config
from behave_data.errors import FixtureNotFoundError, OptionalDependencyError
from behave_data.secrets import resolve_placeholder


class TestEnvPlaceholder:
    def test_env_var_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_SECRET_VAR", "secret_value")
        result = resolve_placeholder("env:TEST_SECRET_VAR")
        assert result == "secret_value"

    def test_env_var_not_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NONEXISTENT_VAR_12345", raising=False)
        result = resolve_placeholder("env:NONEXISTENT_VAR_12345")
        assert result is None

    def test_env_empty_var_name_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            resolve_placeholder("env:")


class TestFilePlaceholder:
    def test_file_exists(self, tmp_path: Path) -> None:
        secret_file = tmp_path / "api_key.txt"
        secret_file.write_text("my_api_key\n", encoding="utf-8")
        config = Config(secret_path=str(tmp_path))
        result = resolve_placeholder("file:api_key.txt", config)
        assert result == "my_api_key"

    def test_file_not_exists(self, tmp_path: Path) -> None:
        config = Config(secret_path=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            resolve_placeholder("file:nonexistent.txt", config)

    def test_file_content_stripped(self, tmp_path: Path) -> None:
        secret_file = tmp_path / "key.txt"
        secret_file.write_text("  secret_value  \n", encoding="utf-8")
        config = Config(secret_path=str(tmp_path))
        result = resolve_placeholder("file:key.txt", config)
        assert result == "secret_value"

    def test_file_empty_path_raises(self, tmp_path: Path) -> None:
        config = Config(secret_path=str(tmp_path))
        with pytest.raises(ValueError, match="cannot be empty"):
            resolve_placeholder("file:", config)

    def test_file_path_traversal_raises(self, tmp_path: Path) -> None:
        config = Config(secret_path=str(tmp_path))
        with pytest.raises(ValueError, match="path traversal"):
            resolve_placeholder("file:../../etc/passwd", config)


class TestRefPlaceholder:
    def test_ref_resolves_fixture(self) -> None:
        manager = MagicMock()
        manager.fixture.return_value = {"name": "Alice"}
        result = resolve_placeholder("ref:user", manager=manager)
        assert "Alice" in result

    def test_ref_fixture_not_found(self) -> None:
        manager = MagicMock()
        manager.fixture.side_effect = FixtureNotFoundError("user")
        with pytest.raises(FixtureNotFoundError):
            resolve_placeholder("ref:user", manager=manager)

    def test_ref_without_manager_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot resolve 'ref:'"):
            resolve_placeholder("ref:user")


class TestNonPlaceholder:
    def test_plain_value_returned_as_is(self) -> None:
        result = resolve_placeholder("just_a_string")
        assert result == "just_a_string"

    def test_empty_string_returned(self) -> None:
        result = resolve_placeholder("")
        assert result == ""


class TestSecretBackend:
    def test_secret_env_backend(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_SECRET", "env_secret_val")
        config = Config(secret_backend="env")
        result = resolve_placeholder("secret:MY_SECRET", config)
        assert result == "env_secret_val"

    def test_secret_file_backend(self, tmp_path: Path) -> None:
        secret_file = tmp_path / "api_key"
        secret_file.write_text("file_secret_val", encoding="utf-8")
        config = Config(secret_backend="file", secret_path=str(tmp_path))
        result = resolve_placeholder("secret:api_key", config)
        assert result == "file_secret_val"

    def test_secret_file_not_found(self, tmp_path: Path) -> None:
        config = Config(secret_backend="file", secret_path=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            resolve_placeholder("secret:nonexistent", config)

    def test_secret_file_path_traversal_raises(self, tmp_path: Path) -> None:
        config = Config(secret_backend="file", secret_path=str(tmp_path))
        with pytest.raises(ValueError, match="path traversal"):
            resolve_placeholder("secret:../../etc/passwd", config)

    def test_secret_unknown_backend(self) -> None:
        config = Config(secret_backend="invalid")
        with pytest.raises(ValueError, match="Unknown secret backend"):
            resolve_placeholder("secret:foo", config)

    def test_secret_vault_not_installed(self) -> None:
        import sys

        config = Config(secret_backend="vault")
        with (
            patch.dict(sys.modules, {"hvac": None}),
            pytest.raises(OptionalDependencyError, match="hvac"),
        ):
            resolve_placeholder("secret:foo", config)

    def test_secret_aws_not_installed(self) -> None:
        import sys

        config = Config(secret_backend="aws")
        with (
            patch.dict(sys.modules, {"boto3": None}),
            pytest.raises(OptionalDependencyError, match="boto3"),
        ):
            resolve_placeholder("secret:foo", config)
