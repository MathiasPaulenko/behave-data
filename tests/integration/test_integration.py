"""Integration test runner for behave-data features."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_integration_features() -> None:
    """Run behave with the integration features directory and assert all pass."""
    features_dir = Path(__file__).parent / "features"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "behave",
            str(features_dir),
            "--no-color",
            "--format=progress",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent),
        timeout=60,
    )
    assert result.returncode == 0, (
        f"Behave integration tests failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
