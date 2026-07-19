"""SQL loader for behave-data."""

from __future__ import annotations

from typing import Any

from behave_data.config import Config
from behave_data.errors import OptionalDependencyError


class SqlLoader:
    """Load data from SQL queries using SQLAlchemy."""

    def load(self, source: str, config: Config) -> list[dict[str, Any]]:
        """Execute a SQL query and return results as list of dicts.

        Args:
            source: SQL query string. Optionally prefixed with a db name
                from ``config.db_connections`` followed by a colon, e.g.
                ``"reporting:SELECT * FROM users"``. If the prefix does not
                match a configured db, the whole source is used as the query
                with the ``"default"`` database.
            config: Configuration with db_connections mapping.

        Returns:
            List of dicts, one per row.

        Raises:
            OptionalDependencyError: If SQLAlchemy is not installed.
            KeyError: If the database name is not in config.db_connections.
        """
        try:
            import sqlalchemy
        except ImportError:
            raise OptionalDependencyError(
                "sqlalchemy",
                "SQL loading",
                "pip install behave-data[sql]",
            ) from None

        db_name = "default"
        query = source
        if ":" in source:
            candidate, _, rest = source.partition(":")
            if candidate in config.db_connections:
                db_name = candidate
                query = rest

        connection_string = config.db_connections.get(db_name)
        if connection_string is None:
            raise KeyError(f"Database '{db_name}' not found in config.db_connections")

        engine = sqlalchemy.create_engine(connection_string)
        try:
            with engine.connect() as conn:
                result = conn.execute(sqlalchemy.text(query))
                columns = list(result.keys())
                return [dict(zip(columns, row, strict=False)) for row in result]
        finally:
            engine.dispose()
