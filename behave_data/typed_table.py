"""TypedTableWrapper — extends TableWrapper with type conversion and null handling."""

from __future__ import annotations

from typing import Any

from behave_tables.wrapper import TableLike, TableWrapper

from behave_data.config import Config
from behave_data.null import get_column_markers, resolve_null
from behave_data.types import convert_cell, parse_column_header


class TypedTableWrapper(TableWrapper):
    """Extends TableWrapper with column typing, null resolution, and conversions.

    Adds ``typed_dicts()``, ``typed_objects()``, ``clean_headers()``,
    ``to_dict()``, ``to_lists()``, and ``to_pandas()`` on top of the
    base TableWrapper API (as_dicts, as_models, transpose, etc.).
    """

    def __init__(self, table: TableLike, config: Config | None = None) -> None:
        """Initialize the typed wrapper.

        Args:
            table: A table-like object with ``headings`` and ``rows``.
            config: Configuration for null markers and type overrides.
        """
        super().__init__(table)
        self._config = config or Config()

    def clean_headers(self) -> list[str]:
        """Return clean column names without type annotations.

        Parses type annotations from headers like ``"age:int"``.

        Returns:
            A list of clean column name strings.
        """
        return [parse_column_header(h)[0] for h in self.headers]

    def typed_dicts(self, config: Config | None = None) -> list[dict[str, Any]]:
        """Return all rows with type conversion and null resolution applied.

        Null resolution happens before type conversion. Null has priority
        over type: a null value returns ``None`` even if a converter exists.

        Args:
            config: Override config for this call. If None, uses the
                config passed to ``__init__``.

        Returns:
            A list of dicts with typed values.
        """
        cfg = config or self._config
        result: list[dict[str, Any]] = []

        for row in self._rows:
            typed_row: dict[str, Any] = {}
            for header in self.headers:
                clean_name, converter, _nullable = parse_column_header(header)
                raw_value = row.get(header, "")
                col_markers = get_column_markers(clean_name, cfg)
                resolved = resolve_null(raw_value, cfg.null_markers, col_markers)
                if resolved is None:
                    typed_row[clean_name] = None
                elif converter is not None:
                    typed_row[clean_name] = convert_cell(resolved, converter, clean_name)
                else:
                    typed_row[clean_name] = resolved
            result.append(typed_row)

        return result

    def typed_objects(self, cls: type, config: Config | None = None) -> list[Any]:
        """Convert all rows to model instances using typed values.

        Uses ``cls(**d)`` for each dict from ``typed_dicts()``.

        Args:
            cls: A class to instantiate (e.g. dataclass or Pydantic model).
            config: Override config for this call.

        Returns:
            A list of model instances.
        """
        return [cls(**d) for d in self.typed_dicts(config)]

    def to_dict(self, config: Config | None = None) -> dict[Any, Any]:
        """Return the table as a key-value dict.

        Requires exactly 2 columns. The first column is the key, the
        second is the value. Both are typed.

        Args:
            config: Override config for this call.

        Returns:
            A dict mapping typed keys to typed values.

        Raises:
            ValueError: If the table does not have exactly 2 columns.
        """
        if len(self.headers) != 2:
            raise ValueError(f"to_dict() requires exactly 2 columns, got {len(self.headers)}")
        typed_rows = self.typed_dicts(config)
        clean_names = self.clean_headers()
        key_name, value_name = clean_names
        return {row[key_name]: row[value_name] for row in typed_rows}

    def to_lists(self, config: Config | None = None) -> list[list[Any]]:
        """Return the table as a list of lists with typed values.

        Each inner list is ``list(row.values())`` from ``typed_dicts()``.

        Args:
            config: Override config for this call.

        Returns:
            A list of lists: [row1_values, row2_values, ...].
        """
        return [list(row.values()) for row in self.typed_dicts(config)]

    def to_pandas(self, config: Config | None = None) -> Any:
        """Return the table as a pandas DataFrame.

        Requires the ``pandas`` optional dependency.

        Args:
            config: Override config for this call.

        Returns:
            A pandas DataFrame with typed values.

        Raises:
            OptionalDependencyError: If pandas is not installed.
        """
        from behave_data.errors import OptionalDependencyError

        try:
            import pandas as pd
        except ImportError:
            raise OptionalDependencyError(
                "pandas",
                "to_pandas()",
                "pip install behave-data[pandas]",
            ) from None

        return pd.DataFrame(self.typed_dicts(config))


def typed_wrap(table: TableLike, config: Config | None = None) -> TypedTableWrapper:
    """Convenience function to wrap a table in a TypedTableWrapper.

    Args:
        table: A table-like object with ``headings`` and ``rows``.
        config: Configuration for null markers and type overrides.

    Returns:
        A TypedTableWrapper instance.
    """
    return TypedTableWrapper(table, config)
