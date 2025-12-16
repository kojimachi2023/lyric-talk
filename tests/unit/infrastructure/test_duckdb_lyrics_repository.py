"""Tests for DuckDB LyricsRepository implementation."""

from datetime import datetime

from src.domain.models.lyrics_corpus import LyricsCorpus
from src.infrastructure.database.duckdb_lyrics_repository import (
    DuckDBLyricsRepository,
)


def test_save_and_find_by_id(temp_db):
    """Test LyricsRepository save and find by ID operations."""
    repo = DuckDBLyricsRepository(str(temp_db))

    # Create test corpus
    corpus = LyricsCorpus(
        lyrics_corpus_id="corpus-001",
        title="Test Song",
        artist="Test Artist",
        content_hash="abc123",
        created_at=datetime.now(),
    )

    # Save corpus
    repo.save(corpus)

    # Find by id
    result = repo.find_by_id("corpus-001")
    assert result is not None
    assert result.title == "Test Song"
    assert result.artist == "Test Artist"


def test_find_by_content_hash(temp_db):
    """Test finding corpus by content hash."""
    repo = DuckDBLyricsRepository(str(temp_db))

    # Create test corpus
    corpus = LyricsCorpus(
        lyrics_corpus_id="corpus-001",
        title="Test Song",
        artist="Test Artist",
        content_hash="abc123",
        created_at=datetime.now(),
    )
    repo.save(corpus)

    # Find by content_hash
    result = repo.find_by_content_hash("abc123")
    assert result is not None
    assert result.title == "Test Song"

    # Non-existent hash
    result = repo.find_by_content_hash("nonexistent")
    assert result is None


def test_find_by_title(temp_db):
    """Test finding corpus by title (partial match)."""
    repo = DuckDBLyricsRepository(str(temp_db))

    # Create test corpora
    corpus1 = LyricsCorpus(
        lyrics_corpus_id="corpus-001",
        title="Test Song One",
        content_hash="hash1",
        created_at=datetime.now(),
    )
    corpus2 = LyricsCorpus(
        lyrics_corpus_id="corpus-002",
        title="Another Test",
        content_hash="hash2",
        created_at=datetime.now(),
    )
    repo.save(corpus1)
    repo.save(corpus2)

    # Find by title (partial match)
    results = repo.find_by_title("Test")
    assert len(results) == 2

    results = repo.find_by_title("Song")
    assert len(results) == 1
    assert results[0].title == "Test Song One"


def test_delete_corpus(temp_db):
    """Test deleting a corpus."""
    repo = DuckDBLyricsRepository(str(temp_db))

    # Create and save corpus
    corpus = LyricsCorpus(
        lyrics_corpus_id="corpus-001",
        title="Test Song",
        content_hash="abc123",
        created_at=datetime.now(),
    )
    repo.save(corpus)

    # Verify it exists
    result = repo.find_by_id("corpus-001")
    assert result is not None

    # Delete it
    repo.delete("corpus-001")

    # Verify it's gone
    result = repo.find_by_id("corpus-001")
    assert result is None


def test_save_updates_existing(temp_db):
    """Test that saving updates an existing corpus."""
    repo = DuckDBLyricsRepository(str(temp_db))

    # Create and save initial corpus
    corpus = LyricsCorpus(
        lyrics_corpus_id="corpus-001",
        title="Original Title",
        content_hash="hash1",
        created_at=datetime.now(),
    )
    repo.save(corpus)

    # Update and save again
    corpus.title = "Updated Title"
    repo.save(corpus)

    # Verify update
    result = repo.find_by_id("corpus-001")
    assert result is not None
    assert result.title == "Updated Title"
