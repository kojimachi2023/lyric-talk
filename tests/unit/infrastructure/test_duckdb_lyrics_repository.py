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


def test_list_lyric_corpora_empty(temp_db):
    """Test list_lyric_corpora with empty database."""
    repo = DuckDBLyricsRepository(str(temp_db))

    # Empty database should return empty list
    result = repo.list_lyrics_corpora(10)
    assert result == []


def test_list_lyric_corpora_single(temp_db):
    """Test list_lyric_corpora with single corpus."""
    repo = DuckDBLyricsRepository(str(temp_db))

    # Create and save corpus
    corpus = LyricsCorpus(
        lyrics_corpus_id="corpus-001",
        title="Test Song",
        artist="Test Artist",
        content_hash="hash1",
        created_at=datetime(2025, 1, 1, 12, 0, 0),
    )
    repo.save(corpus)

    # List should return the corpus
    result = repo.list_lyrics_corpora(10)
    assert len(result) == 1
    assert result[0].lyrics_corpus_id == "corpus-001"
    assert result[0].title == "Test Song"


def test_list_lyric_corpora_multiple_ordered(temp_db):
    """Test list_lyric_corpora with multiple corpora in descending order."""
    repo = DuckDBLyricsRepository(str(temp_db))

    # Create corpora with different timestamps
    corpus1 = LyricsCorpus(
        lyrics_corpus_id="corpus-001",
        title="Old Song",
        content_hash="hash1",
        created_at=datetime(2025, 1, 1, 10, 0, 0),
    )
    corpus2 = LyricsCorpus(
        lyrics_corpus_id="corpus-002",
        title="New Song",
        content_hash="hash2",
        created_at=datetime(2025, 1, 1, 12, 0, 0),
    )
    corpus3 = LyricsCorpus(
        lyrics_corpus_id="corpus-003",
        title="Middle Song",
        content_hash="hash3",
        created_at=datetime(2025, 1, 1, 11, 0, 0),
    )

    # Save in random order
    repo.save(corpus1)
    repo.save(corpus2)
    repo.save(corpus3)

    # List should be in descending order (newest first)
    result = repo.list_lyrics_corpora(10)
    assert len(result) == 3
    assert result[0].lyrics_corpus_id == "corpus-002"  # Newest
    assert result[0].title == "New Song"
    assert result[1].lyrics_corpus_id == "corpus-003"  # Middle
    assert result[2].lyrics_corpus_id == "corpus-001"  # Oldest


def test_list_lyric_corpora_respects_limit(temp_db):
    """Test list_lyric_corpora respects the limit parameter."""

    repo = DuckDBLyricsRepository(str(temp_db))

    # Create 5 corpora
    for i in range(5):
        corpus = LyricsCorpus(
            lyrics_corpus_id=f"corpus-{i:03d}",
            title=f"Song {i}",
            content_hash=f"hash{i}",
            created_at=datetime(2025, 1, 1, 10 + i, 0, 0),
        )
        repo.save(corpus)

    # Request only 3
    result = repo.list_lyrics_corpora(3)
    assert len(result) == 3
    # Should get the 3 newest
    assert result[0].lyrics_corpus_id == "corpus-004"
    assert result[1].lyrics_corpus_id == "corpus-003"
    assert result[2].lyrics_corpus_id == "corpus-002"
