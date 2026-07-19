"""RawTable — access to full table data without assuming a header row."""

from __future__ import annotations

from typing import overload

from behave_tables.wrapper import TableLike


class RawTable:
    """Wraps a table-like object providing access to all rows including the header.

    Unlike TableWrapper which treats the first row as headers, RawTable
    combines the headings (which Behave treats as the first row) with the
    remaining rows into a single list. This is useful for tables that
    don't have a header row, or when you need access to the header row
    as data.
    """

    def __init__(self, table: TableLike) -> None:
        """Initialize the RawTable from a table-like object.

        Args:
            table: A table-like object with ``headings`` and ``rows``.
        """
        headings = list(table.headings)
        rows: list[list[str]] = [headings]
        heading_count = len(headings)

        for row in table.rows:
            if isinstance(row, (list, tuple)):
                row_copy = list(row)
                if len(row_copy) < heading_count:
                    row_copy.extend([""] * (heading_count - len(row_copy)))
                rows.append(row_copy)
            else:
                try:
                    as_dict = row.as_dict()
                except (AttributeError, TypeError):
                    as_dict = row if isinstance(row, dict) else None
                if isinstance(as_dict, dict):
                    rows.append([str(as_dict.get(h, "")) for h in headings])
                else:
                    values: list[str] = []
                    for h in headings:
                        try:
                            values.append(str(row[h]))
                        except (KeyError, IndexError, TypeError):
                            values.append("")
                    rows.append(values)
        self._rows: list[list[str]] = rows

    @property
    def rows(self) -> list[list[str]]:
        """Return a copy of all rows (including the header row).

        Returns:
            A copy of all rows as lists of strings.
        """
        return [list(r) for r in self._rows]

    @property
    def raw_rows(self) -> list[list[str]]:
        """Alias for :attr:`rows`.

        Returns:
            A copy of all rows as lists of strings.
        """
        return self.rows

    def to_dicts(self, headers: list[str]) -> list[dict[str, str]]:
        """Build a list of dicts using the provided headers.

        If a header has more columns than a row, missing values are
        filled with empty strings.

        Args:
            headers: Column names to use as dict keys.

        Returns:
            A list of dicts mapping header names to cell values.
        """
        result: list[dict[str, str]] = []
        for row in self._rows:
            d: dict[str, str] = {}
            for i, h in enumerate(headers):
                d[h] = row[i] if i < len(row) else ""
            result.append(d)
        return result

    def to_lists(self) -> list[list[str]]:
        """Return all rows as a list of lists.

        Returns:
            A copy of all rows as lists of strings.
        """
        return [list(r) for r in self._rows]

    def __len__(self) -> int:
        """Return the total number of rows."""
        return len(self._rows)

    @overload
    def __getitem__(self, index: int) -> list[str]: ...

    @overload
    def __getitem__(self, index: slice) -> list[list[str]]: ...

    def __getitem__(self, index: int | slice) -> list[str] | list[list[str]]:
        """Return the row at the given index.

        Args:
            index: Zero-based row index or slice.

        Returns:
            A copy of the row as a list, or a list of lists for a slice.

        Raises:
            IndexError: If the index is out of range.
        """
        if isinstance(index, slice):
            return [list(r) for r in self._rows[index]]
        return list(self._rows[index])

    def __repr__(self) -> str:
        return f"RawTable(rows={len(self)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RawTable):
            return NotImplemented
        return self._rows == other._rows

    def __hash__(self) -> int:
        raise TypeError("unhashable type: 'RawTable'")


def raw_table(table: TableLike) -> RawTable:
    """Convenience function to create a RawTable.

    Args:
        table: A table-like object with ``headings`` and ``rows``.

    Returns:
        A RawTable instance.
    """
    return RawTable(table)
