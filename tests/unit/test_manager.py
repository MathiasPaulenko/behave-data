"""Tests for behave_data.manager — DataManager and masking."""

from __future__ import annotations

import pytest

from behave_data.config import Config
from behave_data.manager import DataManager


class TestResolve:
    def test_resolve_non_string(self) -> None:
        dm = DataManager()
        assert dm.resolve(42) == 42
        assert dm.resolve(None) is None

    def test_resolve_plain_string(self) -> None:
        dm = DataManager()
        assert dm.resolve("hello") == "hello"

    def test_resolve_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_DM_VAR", "dm_value")
        dm = DataManager()
        assert dm.resolve("env:TEST_DM_VAR") == "dm_value"

    def test_resolve_file(self, tmp_path: object) -> None:
        from pathlib import Path

        p = tmp_path if isinstance(tmp_path, Path) else Path(str(tmp_path))
        secret_file = p / "key.txt"
        secret_file.write_text("file_secret", encoding="utf-8")
        config = Config(secret_path=str(p))
        dm = DataManager(config)
        assert dm.resolve("file:key.txt") == "file_secret"


class TestMasking:
    def test_mask_secret_resolved(self) -> None:
        dm = DataManager()
        dm._secret_hashes.add(hash("my_secret"))
        assert dm.mask("my_secret") == "***"

    def test_mask_non_secret(self) -> None:
        dm = DataManager()
        assert dm.mask("plain_value") == "plain_value"

    def test_mask_none(self) -> None:
        dm = DataManager()
        assert dm.mask(None) is None

    def test_two_different_secrets_no_collision(self) -> None:
        dm = DataManager()
        dm._secret_hashes.add(hash("secret_a"))
        dm._secret_hashes.add(hash("secret_b"))
        assert dm.mask("secret_a") == "***"
        assert dm.mask("secret_b") == "***"
        assert dm.mask("secret_c") == "secret_c"

    def test_mask_after_resolve_env_not_masked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DM_TEST", "env_value")
        dm = DataManager()
        dm.resolve("env:DM_TEST")
        assert dm.mask("env_value") == "env_value"

    def test_mask_after_resolve_secret_is_masked(self) -> None:
        config = Config(secret_backend="env")
        dm = DataManager(config)
        import os

        os.environ["DM_SECRET_TEST"] = "super_secret"
        dm.resolve("secret:DM_SECRET_TEST")
        assert dm.mask("super_secret") == "***"
        del os.environ["DM_SECRET_TEST"]

    def test_hash_stable(self) -> None:
        assert hash("value") == hash("value")
        dm = DataManager()
        dm._secret_hashes.add(hash("value"))
        assert dm.mask("value") == "***"

    def test_mask_after_resolve_file_not_masked(self, tmp_path: object) -> None:
        from pathlib import Path

        p = tmp_path if isinstance(tmp_path, Path) else Path(str(tmp_path))
        secret_file = p / "key.txt"
        secret_file.write_text("file_val", encoding="utf-8")
        config = Config(secret_path=str(p))
        dm = DataManager(config)
        dm.resolve("file:key.txt")
        assert dm.mask("file_val") == "file_val"


class TestFixturesAndBuilders:
    def test_fixture_delegates(self) -> None:
        dm = DataManager()
        dm.fixtures.register("user", lambda: {"name": "Alice"})
        assert dm.fixture("user")["name"] == "Alice"

    def test_build_delegates(self) -> None:
        dm = DataManager()
        dm.builders.register("user", lambda o: {"name": "Bob", **o})
        assert dm.build("user")["name"] == "Bob"
