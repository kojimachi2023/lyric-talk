"""Pytest fixtures for infrastructure tests."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from src.domain.models.lyrics_corpus import LyricsCorpus
from src.infrastructure.database.duckdb_unit_of_work import DuckDBUnitOfWork
from src.infrastructure.database.schema import initialize_database


@pytest.fixture
def temp_db() -> Generator[Path, None, None]:
    """Create a temporary DuckDB database for testing.

    Yields:
        Path to temporary database file
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = initialize_database(str(db_path))
        conn.close()
        yield db_path


@pytest.fixture
def unit_of_work(temp_db: Path) -> Generator[DuckDBUnitOfWork, None, None]:
    """Create a Unit of Work for testing.

    Args:
        temp_db: Path to temporary database

    Yields:
        DuckDBUnitOfWork instance (already entered context)
    """
    uow = DuckDBUnitOfWork(str(temp_db))
    with uow:
        yield uow
        uow.commit()


@pytest.fixture
def unit_of_work_with_corpus(
    temp_db: Path,
) -> Generator[tuple[DuckDBUnitOfWork, str], None, None]:
    """Create a Unit of Work with a test corpus.

    Args:
        temp_db: Path to temporary database

    Yields:
        Tuple of (UnitOfWork, corpus_id)
    """
    uow = DuckDBUnitOfWork(str(temp_db))
    with uow:
        corpus = LyricsCorpus(
            lyrics_corpus_id="corpus-001",
            content_hash="test-hash",
            title="Test Corpus",
            created_at=datetime.now(),
        )
        uow.lyrics_repository.save(corpus)
        uow.commit()

    # Start a new UoW for the test
    uow = DuckDBUnitOfWork(str(temp_db))
    with uow:
        yield uow, "corpus-001"
        uow.commit()
