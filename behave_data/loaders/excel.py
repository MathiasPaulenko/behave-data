"""Excel loader for behave-data."""

from __future__ import annotations

from typing import Any

from behave_data.config import Config
from behave_data.errors import OptionalDependencyError


class ExcelLoader:
    """Load data from Excel (.xlsx) files using openpyxl."""

    def load(self, source: str, config: Config) -> list[dict[str, Any]]:
        """Load Excel data from a file path.

        First row is treated as headers.

        Args:
            source: Path to the Excel file.
            config: Configuration (unused for Excel, but required by Protocol).

        Returns:
            List of dicts, one per data row.

        Raises:
            OptionalDependencyError: If openpyxl is not installed.
        """
        try:
            import openpyxl
        except ImportError:
            raise OptionalDependencyError(
                "openpyxl",
                "Excel loading",
                "pip install behave-data[excel]",
            ) from None

        wb = openpyxl.load_workbook(source, read_only=True)
        try:
            ws = wb.active
            if ws is None:
                return []
            rows = list(ws.iter_rows(values_only=True))
        finally:
            wb.close()

        if not rows:
            return []

        headers = [str(h) if h is not None else "" for h in rows[0]]
        header_count = len(headers)
        result: list[dict[str, Any]] = []
        for row in rows[1:]:
            row_dict: dict[str, Any] = {}
            for i in range(max(len(row), header_count)):
                key = headers[i] if i < header_count else f"col_{i}"
                row_dict[key] = row[i] if i < len(row) else None
            result.append(row_dict)
        return result
