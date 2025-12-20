"""Pytest fixtures for infrastructure tests."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from src.domain.models.lyrics_corpus import LyricsCorpus
from src.infrastructure.database.duckdb_lyrics_repository import (
    DuckDBLyricsRepository,
)
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
def temp_db_with_corpus(temp_db: Path) -> tuple[Path, str]:
    """Create a temporary database with a test corpus.

    Args:
        temp_db: Path to temporary database

    Returns:
        Tuple of (db_path, corpus_id)
    """
    lyrics_repo = DuckDBLyricsRepository(str(temp_db))
    corpus = LyricsCorpus(
        lyrics_corpus_id="corpus-001",
        content_hash="test-hash",
        title="Test Corpus",
        created_at=datetime.now(),
    )
    lyrics_repo.save(corpus)
    return temp_db, corpus.lyrics_corpus_id
