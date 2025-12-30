"""DuckDB implementation of Unit of Work pattern."""

import duckdb

from src.domain.repositories.unit_of_work import UnitOfWork
from src.infrastructure.database.duckdb_lyric_token_repository import (
    DuckDBLyricTokenRepository,
)
from src.infrastructure.database.duckdb_lyrics_repository import DuckDBLyricsRepository
from src.infrastructure.database.duckdb_match_repository import DuckDBMatchRepository


class DuckDBUnitOfWork(UnitOfWork):
    """DuckDB implementation of Unit of Work.

    単一のDuckDBコネクション上でトランザクションを管理し、
    各リポジトリに同一コネクションを注入する。

    Usage:
        uow = DuckDBUnitOfWork(db_path)
        with uow:
            uow.lyrics_repository.save(corpus)
            uow.lyric_token_repository.save_many(tokens)
            uow.commit()
    """

    def __init__(self, db_path: str):
        """Initialize Unit of Work with database path.

        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path
        self._connection: duckdb.DuckDBPyConnection | None = None
        self._committed = False

    @property
    def lyrics_repository(self) -> DuckDBLyricsRepository:
        """Get lyrics repository."""
        if self._lyrics_repository is None:
            raise RuntimeError("Unit of Work not started. Use 'with' statement.")
        return self._lyrics_repository

    @property
    def lyric_token_repository(self) -> DuckDBLyricTokenRepository:
        """Get lyric token repository."""
        if self._lyric_token_repository is None:
            raise RuntimeError("Unit of Work not started. Use 'with' statement.")
        return self._lyric_token_repository

    @property
    def match_repository(self) -> DuckDBMatchRepository:
        """Get match repository."""
        if self._match_repository is None:
            raise RuntimeError("Unit of Work not started. Use 'with' statement.")
        return self._match_repository

    def __enter__(self) -> "DuckDBUnitOfWork":
        """Start transaction and initialize repositories."""
        self._connection = duckdb.connect(self.db_path)
        self._connection.begin()
        self._committed = False

        # Create repositories with injected connection
        self._lyrics_repository = DuckDBLyricsRepository(self._connection)
        self._lyric_token_repository = DuckDBLyricTokenRepository(self._connection)
        self._match_repository = DuckDBMatchRepository(self._connection)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End transaction and close connection.

        If an exception occurred or commit() was not called, rollback.
        """
        if self._connection is None:
            return

        try:
            if exc_type is not None:
                # Exception occurred, rollback
                self.rollback()
            elif not self._committed:
                # No exception but not committed, rollback
                self.rollback()
        finally:
            self._connection.close()
            self._connection = None
            self._lyrics_repository = None
            self._lyric_token_repository = None
            self._match_repository = None

    def commit(self) -> None:
        """Commit the transaction."""
        if self._connection is None:
            raise RuntimeError("Unit of Work not started. Use 'with' statement.")
        self._connection.commit()
        self._committed = True

    def rollback(self) -> None:
        """Rollback the transaction."""
        if self._connection is None:
            raise RuntimeError("Unit of Work not started. Use 'with' statement.")
        try:
            self._connection.rollback()
        except Exception:
            pass  # Ignore rollback errors (connection may already be closed)
