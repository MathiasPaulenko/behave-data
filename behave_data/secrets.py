"""Secret and placeholder resolution for behave-data."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from behave_data.config import Config
from behave_data.errors import FixtureNotFoundError, OptionalDependencyError


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
        return os.environ.get(var_name)

    if value.startswith("file:"):
        file_path = value[5:]
        full_path = Path(cfg.secret_path) / file_path
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
        if isinstance(data, dict):
            return str(data)
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
        return response["data"]["data"].get("value")

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
        return response.get("SecretString")

    raise ValueError(f"Unknown secret backend: {backend!r}")
