"""Secret and placeholder resolution for behave-data."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from behave_data.config import Config
from behave_data.errors import FixtureNotFoundError, OptionalDependencyError


def _validate_path_within_base(path: Path, base: Path) -> None:
    """Validate that a resolved path stays within the base directory.

    Prevents path traversal attacks (e.g. ``../../etc/passwd``).

    Args:
        path: The resolved absolute path to check.
        base: The base directory that path must stay within.

    Raises:
        ValueError: If the path escapes the base directory.
    """
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError:
        raise ValueError(
            f"Path '{path}' escapes base directory '{base}' — path traversal not allowed"
        ) from None


def resolve_placeholder(
    value: str,
    config: Config | None = None,
    manager: Any = None,
) -> str | None:
    """Resolve a placeholder string to its actual value.

    Supported prefixes:
        - ``env:VAR_NAME`` — read from environment variable.
        - ``file:relative/path`` — read from file, stripped.
        - ``ref:fixture_name`` — resolve via DataManager.fixture().
        - ``secret:name`` — resolve via configured backend.

    Args:
        value: The placeholder string.
        config: Configuration with secret_path and secret_backend.
        manager: DataManager instance for ``ref:`` resolution.

    Returns:
        The resolved value, or None if the env var doesn't exist.

    Raises:
        ValueError: If ``ref:`` is used without a manager.
        FixtureNotFoundError: If ``ref:`` fixture is not registered.
        FileNotFoundError: If ``file:`` path doesn't exist.
        OptionalDependencyError: If vault/aws backend dependency missing.
    """
    cfg = config if config is not None else Config()

    if value.startswith("env:"):
        var_name = value[4:]
        if not var_name:
            raise ValueError("Environment variable name cannot be empty in 'env:' placeholder")
        return os.environ.get(var_name)

    if value.startswith("file:"):
        file_path = value[5:]
        if not file_path:
            raise ValueError("File path cannot be empty in 'file:' placeholder")
        full_path = Path(cfg.secret_path) / file_path
        _validate_path_within_base(full_path, Path(cfg.secret_path))
        if not full_path.exists():
            raise FileNotFoundError(f"Secret file not found: {full_path}")
        return full_path.read_text(encoding="utf-8").strip()

    if value.startswith("ref:"):
        if manager is None:
            raise ValueError("Cannot resolve 'ref:' placeholder without a manager")
        fixture_name = value[4:]
        data = manager.fixture(fixture_name)
        if data is None:
            raise FixtureNotFoundError(fixture_name)
        return str(data)

    if value.startswith("secret:"):
        return _resolve_secret(value[7:], cfg)

    return value


def _resolve_secret(name: str, config: Config) -> str | None:
    """Resolve a secret via the configured backend.

    Backends: file, env, vault, aws.

    Args:
        name: The secret name.
        config: Configuration with secret_backend and secret_path.

    Returns:
        The secret value.

    Raises:
        FileNotFoundError: If file backend and file not found.
        OptionalDependencyError: If vault/aws dependency missing.
        ValueError: If unknown backend.
    """
    backend = config.secret_backend

    if backend == "file":
        full_path = Path(config.secret_path) / name
        _validate_path_within_base(full_path, Path(config.secret_path))
        if not full_path.exists():
            raise FileNotFoundError(f"Secret file not found: {full_path}")
        return full_path.read_text(encoding="utf-8").strip()

    if backend == "env":
        return os.environ.get(name)

    if backend == "vault":
        try:
            import hvac
        except ImportError:
            raise OptionalDependencyError(
                "hvac",
                "Vault secrets backend",
                "pip install hvac",
            ) from None
        url = os.environ.get("VAULT_ADDR", "http://localhost:8200")
        token = os.environ.get("VAULT_TOKEN", "")
        client = hvac.Client(url=url, token=token)
        response = client.secrets.kv.v2.read_secret_version(path=name)
        result: str | None = response["data"]["data"].get("value")
        return result

    if backend == "aws":
        try:
            import boto3
        except ImportError:
            raise OptionalDependencyError(
                "boto3",
                "AWS Secrets Manager backend",
                "pip install boto3",
            ) from None
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=name)
        aws_result: str | None = response.get("SecretString")
        return aws_result

    raise ValueError(f"Unknown secret backend: {backend!r}")
