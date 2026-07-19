"""TypedTableWrapper — extends TableWrapper with type conversion and null handling."""

from __future__ import annotations

from typing import Any, cast

from behave_tables.wrapper import TableLike, TableWrapper

from behave_data.config import Config
from behave_data.null import get_column_markers, resolve_null
from behave_data.types import TYPE_CONVERTERS, convert_cell, parse_column_header


class TypedTableWrapper(TableWrapper):  # type: ignore[misc]
    """Extends TableWrapper with column typing, null resolution, and conversions.

    Adds ``typed_dicts()``, ``typed_objects()``, ``clean_headers()``,
    ``to_dict()``, ``to_lists()``, and ``to_pandas()`` on top of the
    base TableWrapper API (as_dicts, as_models, transpose, etc.).
    """

    def __init__(self, table: TableLike, config: Config | None = None) -> None:
        """Initialize the typed wrapper.

        Args:
            table: A table-like object with ``headings`` and ``rows``.
                Can also be an existing ``TableWrapper``/``TypedTableWrapper``.
            config: Configuration for null markers and type overrides.
        """
        if isinstance(table, TableWrapper):
            # Re-wrap an existing wrapper without re-extracting rows.
            self._table = table._table
            self._rows = [dict(r) for r in table._rows]
        else:
            super().__init__(table)
        self._config = config or Config()

    @property
    def headings(self) -> list[str]:
        """Return a copy of the raw table headings.

        Alias for :attr:`headers` that satisfies the ``TableLike`` protocol.
        """
        return cast("list[str]", self.headers)

    @property
    def rows(self) -> list[dict[str, str]]:
        """Return a copy of the extracted rows as dicts.

        Satisfies the ``TableLike`` protocol and makes ``TypedTableWrapper``
        usable with ``raw_table`` and ``diff``.
        """
        return [dict(r) for r in self._rows]

    def clean_headers(self) -> list[str]:
        """Return clean column names without type annotations.

        Parses type annotations from headers like ``"age:int"``.

        Returns:
            A list of clean column name strings.
        """
        return [parse_column_header(h)[0] for h in self.headers]

    def _resolve_column_type(self, header: str, cfg: Config) -> tuple[str, Any, bool, str]:
        """Determine the converter, type name, and nullable flag for a column.

        Checks type overrides first, then falls back to the header annotation.

        Args:
            header: The raw column header (e.g. ``"age:int?"``).
            cfg: The active config to check for type overrides.

        Returns:
            A tuple of ``(clean_name, converter, nullable, type_name)``.
            ``converter`` is ``None`` when no type is specified.

        Raises:
            ValueError: If a type override specifies an unknown or empty type.
        """
        clean_name, converter, nullable = parse_column_header(header)
        type_name = ""
        if clean_name in cfg.type_overrides:
            type_spec = cfg.type_overrides[clean_name].strip()
            nullable = type_spec.endswith("?")
            if nullable:
                type_spec = type_spec[:-1].strip()
            type_name = type_spec
            converter = TYPE_CONVERTERS.get(type_spec)
            if converter is None:
                if type_spec:
                    raise ValueError(
                        f"Unknown type '{type_spec}' in type_overrides for column "
                        f"'{clean_name}'. Register it with register_type() or use "
                        f"one of: {', '.join(sorted(TYPE_CONVERTERS))}"
                    )
                raise ValueError(f"Empty type name in type_overrides for column '{clean_name}'")
        elif converter is not None:
            type_name = header.rsplit(":", 1)[-1].rstrip("?").strip()
        return clean_name, converter, nullable, type_name

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

        columns: list[tuple[str, str, Any, bool, str, frozenset[str] | None]] = []
        for header in self.headers:
            clean_name, converter, nullable, type_name = self._resolve_column_type(header, cfg)
            col_markers = get_column_markers(clean_name, cfg)
            columns.append((header, clean_name, converter, nullable, type_name, col_markers))

        for row in self._rows:
            typed_row: dict[str, Any] = {}
            for (
                header,
                clean_name,
                converter,
                nullable,
                type_name,
                col_markers,
            ) in columns:
                raw_value = row.get(header, "")
                resolved = resolve_null(raw_value, cfg.null_markers, col_markers)
                if resolved == "" and nullable:
                    resolved = None
                if resolved is None:
                    typed_row[clean_name] = None
                elif converter is not None:
                    typed_row[clean_name] = convert_cell(resolved, converter, clean_name, type_name)
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
