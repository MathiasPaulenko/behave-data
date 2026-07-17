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
            source: SQL query string.
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
        connection_string = config.db_connections.get(db_name)
        if connection_string is None:
            raise KeyError(f"Database '{db_name}' not found in config.db_connections")

        engine = sqlalchemy.create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(source))
            columns = list(result.keys())
            return [dict(zip(columns, row, strict=False)) for row in result]
