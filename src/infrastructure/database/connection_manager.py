"""DuckDB Connection Manager for connection pooling and reuse."""

from contextlib import contextmanager
from typing import Optional

import duckdb


class DuckDBConnectionManager:
    """Manages DuckDB connections with connection reuse.

    This class provides efficient connection management by reusing connections
    instead of creating new ones for each operation. DuckDB connections are
    thread-local and lightweight, but the connection overhead still adds up
    when called hundreds of times.

    Usage:
        # Create manager
        manager = DuckDBConnectionManager(db_path)

        # Use connection (reuses existing connection)
        with manager.get_connection() as conn:
            conn.execute("SELECT ...")

        # Explicitly close when done
        manager.close()
    """

    _instances: dict[str, "DuckDBConnectionManager"] = {}

    def __init__(self, db_path: str):
        """Initialize connection manager.

        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path
        self._connection: Optional[duckdb.DuckDBPyConnection] = None

    @classmethod
    def get_instance(cls, db_path: str) -> "DuckDBConnectionManager":
        """Get or create a singleton instance for the given database path.

        Args:
            db_path: Path to DuckDB database file

        Returns:
            DuckDBConnectionManager instance
        """
        if db_path not in cls._instances:
            cls._instances[db_path] = cls(db_path)
        return cls._instances[db_path]

    @classmethod
    def clear_instances(cls) -> None:
        """Clear all singleton instances. Useful for testing."""
        for instance in cls._instances.values():
            instance.close()
        cls._instances.clear()

    def _ensure_connection(self) -> duckdb.DuckDBPyConnection:
        """Ensure connection exists, creating if necessary."""
        if self._connection is None:
            self._connection = duckdb.connect(self.db_path)
        return self._connection

    @contextmanager
    def get_connection(self):
        """Get a database connection (reuses existing connection).

        Yields:
            DuckDB connection
        """
        conn = self._ensure_connection()
        try:
            yield conn
        except Exception:
            # On error, close and recreate connection on next use
            self.close()
            raise

    def close(self) -> None:
        """Close the connection if open."""
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass  # Ignore errors during close
            self._connection = None
