"""Shared test fixtures — mock behave Table and Row objects."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest


@dataclass
class FakeRow:
    """Mimics behave.model.Row."""

    cells: list[str]
    headings: list[str]

    def as_dict(self) -> dict[str, str]:
        return dict(zip(self.headings, self.cells, strict=True))

    def __getitem__(self, key: str) -> str:
        idx = self.headings.index(key)
        return self.cells[idx]


@dataclass
class FakeTable:
    """Mimics behave.model.Table."""

    headings: list[str]
    rows_cells: list[list[str]] = field(default_factory=list)

    @property
    def rows(self) -> list[FakeRow]:
        return [FakeRow(cells=c, headings=self.headings) for c in self.rows_cells]


def _make_table(
    headings: list[str],
    rows: list[list[str]],
) -> FakeTable:
    """Build a FakeTable for testing."""
    return FakeTable(headings=headings, rows_cells=rows)


@pytest.fixture
def make_table() -> Callable[[list[str], list[list[str]]], FakeTable]:
    """Return a factory that builds FakeTable instances."""
    return _make_table


@pytest.fixture
def mock_context() -> SimpleNamespace:
    """Return a mock context object without a .table attribute."""
    return SimpleNamespace()


@pytest.fixture
def tmp_data_file(
    tmp_path: Path,
) -> Callable[[str, str], Path]:
    """Return a factory that creates temporary data files.

    Args:
        suffix: File extension (e.g. '.csv', '.json').
        content: File content as string.

    Returns:
        Path to the created file. File is auto-cleaned by pytest.
    """

    def _create(suffix: str, content: str) -> Path:
        path = tmp_path / f"data{suffix}"
        path.write_text(content, encoding="utf-8")
        return path

    return _create


@pytest.fixture(autouse=True)
def _restore_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure environment variables modified in tests are restored."""
    yield


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], None]:
    """Return a function that deletes env vars for the test duration."""

    def _del(name: str) -> None:
        monkeypatch.delenv(name, raising=False)

    return _del
