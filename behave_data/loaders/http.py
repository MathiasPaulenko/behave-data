"""HTTP loader for behave-data."""

from __future__ import annotations

from typing import Any

from behave_data.config import Config
from behave_data.errors import OptionalDependencyError


class HttpLoader:
    """Load data from HTTP endpoints using requests."""

    def load(self, source: str, config: Config) -> list[dict[str, Any]]:
        """Fetch data from an HTTP endpoint.

        Source format: ``GET https://api.example.com/users`` or
        ``POST https://api.example.com/users``.

        Args:
            source: HTTP method + URL string.
            config: Configuration (unused for HTTP, but required by Protocol).

        Returns:
            List of dicts from the JSON response.

        Raises:
            OptionalDependencyError: If requests is not installed.
        """
        try:
            import requests
        except ImportError:
            raise OptionalDependencyError(
                "requests",
                "HTTP loading",
                "pip install behave-data[http]",
            ) from None

        parts = source.strip().split(None, 1)
        if not parts or not parts[0]:
            raise ValueError("HTTP source cannot be empty")
        if len(parts) == 2:
            method, url = parts
        else:
            method = "GET"
            url = parts[0]
            if url.upper() in ("GET", "POST"):
                raise ValueError("HTTP source must include a URL after the method")

        method = method.upper()
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError(
                        f"HTTP response list items must be dicts, got {type(item).__name__}"
                    )
            return data
        if isinstance(data, dict):
            return [data]
        raise ValueError(f"HTTP response must be a list or dict, got {type(data).__name__}")
