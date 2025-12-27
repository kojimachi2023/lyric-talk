"""Tests for DuckDB LyricsRepository implementation."""

from datetime import datetime

from src.domain.models.lyrics_corpus import LyricsCorpus
from src.infrastructure.database.duckdb_unit_of_work import DuckDBUnitOfWork


def test_save_and_find_by_id(temp_db):
    """Test LyricsRepository save and find by ID operations."""
    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Create test corpus
        corpus = LyricsCorpus(
            lyrics_corpus_id="corpus-001",
            title="Test Song",
            artist="Test Artist",
            content_hash="abc123",
            created_at=datetime.now(),
        )

        # Save corpus
        uow.lyrics_repository.save(corpus)
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Find by id
        result = uow.lyrics_repository.find_by_id("corpus-001")
        assert result is not None
        assert result.title == "Test Song"
        assert result.artist == "Test Artist"
        assert result.content_hash == "abc123"


def test_find_by_content_hash(temp_db):
    """Test finding corpus by content hash."""
    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Create test corpus
        corpus = LyricsCorpus(
            lyrics_corpus_id="corpus-001",
            title="Test Song",
            artist="Test Artist",
            content_hash="abc123",
            created_at=datetime.now(),
        )
        uow.lyrics_repository.save(corpus)
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Find by content_hash
        result = uow.lyrics_repository.find_by_content_hash("abc123")
        assert result is not None
        assert result.title == "Test Song"
        assert result.artist == "Test Artist"
        assert result.lyrics_corpus_id == "corpus-001"
        assert result.content_hash == "abc123"

        # Non-existent hash
        result = uow.lyrics_repository.find_by_content_hash("nonexistent")
        assert result is None


def test_find_by_title(temp_db):
    """Test finding corpus by title (partial match)."""
    with DuckDBUnitOfWork(str(temp_db)) as uow:
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
        uow.lyrics_repository.save(corpus1)
        uow.lyrics_repository.save(corpus2)
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Find by title (partial match)
        results = uow.lyrics_repository.find_by_title("Test")
        assert len(results) == 2
        assert results[0] == corpus1 or results[0] == corpus2
        assert results[1] == corpus1 or results[1] == corpus2

        results = uow.lyrics_repository.find_by_title("Song")
        assert len(results) == 1
        assert results[0] == corpus1


def test_delete_corpus(temp_db):
    """Test deleting a corpus."""
    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Create and save corpus
        corpus = LyricsCorpus(
            lyrics_corpus_id="corpus-001",
            title="Test Song",
            content_hash="abc123",
            created_at=datetime.now(),
        )
        uow.lyrics_repository.save(corpus)
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Verify it exists
        result = uow.lyrics_repository.find_by_id("corpus-001")
        assert result is not None

        # Delete it
        uow.lyrics_repository.delete("corpus-001")
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Verify it's gone
        result = uow.lyrics_repository.find_by_id("corpus-001")
        assert result is None


def test_save_updates_existing(temp_db):
    """Test that saving updates an existing corpus."""
    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Create and save initial corpus
        corpus = LyricsCorpus(
            lyrics_corpus_id="corpus-001",
            title="Original Title",
            content_hash="hash1",
            created_at=datetime.now(),
        )
        uow.lyrics_repository.save(corpus)
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Update and save again
        corpus = uow.lyrics_repository.find_by_id("corpus-001")
        corpus.title = "Updated Title"
        uow.lyrics_repository.save(corpus)
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Verify update
        result = uow.lyrics_repository.find_by_id("corpus-001")
        assert result is not None
        assert result == corpus


def test_list_lyric_corpora_empty(temp_db):
    """Test list_lyric_corpora with empty database."""
    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Empty database should return empty list
        result = uow.lyrics_repository.list_lyrics_corpora(10)
        assert result == []


def test_list_lyric_corpora_single(temp_db):
    """Test list_lyric_corpora with single corpus."""
    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Create and save corpus
        corpus = LyricsCorpus(
            lyrics_corpus_id="corpus-001",
            title="Test Song",
            artist="Test Artist",
            content_hash="hash1",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        uow.lyrics_repository.save(corpus)
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # List should return the corpus
        result = uow.lyrics_repository.list_lyrics_corpora(10)
        assert len(result) == 1
        assert result[0] == corpus


def test_list_lyric_corpora_multiple_ordered(temp_db):
    """Test list_lyric_corpora with multiple corpora in descending order."""
    with DuckDBUnitOfWork(str(temp_db)) as uow:
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
        uow.lyrics_repository.save(corpus1)
        uow.lyrics_repository.save(corpus2)
        uow.lyrics_repository.save(corpus3)
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # List should be in descending order (newest first)
        result = uow.lyrics_repository.list_lyrics_corpora(10)
        assert len(result) == 3
        assert result[0] == corpus2  # New Song
        assert result[1] == corpus3  # Middle Song
        assert result[2] == corpus1  # Old Song


def test_list_lyric_corpora_respects_limit(temp_db):
    """Test list_lyric_corpora respects the limit parameter."""
    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Create 5 corpora
        for i in range(5):
            corpus = LyricsCorpus(
                lyrics_corpus_id=f"corpus-{i:03d}",
                title=f"Song {i}",
                content_hash=f"hash{i}",
                created_at=datetime(2025, 1, 1, 10 + i, 0, 0),
            )
            uow.lyrics_repository.save(corpus)
        uow.commit()

    with DuckDBUnitOfWork(str(temp_db)) as uow:
        # Request only 3
        result = uow.lyrics_repository.list_lyrics_corpora(3)
        assert len(result) == 3
        # Should get the 3 newest
        assert result[0] == LyricsCorpus(
            lyrics_corpus_id="corpus-004",
            title="Song 4",
            content_hash="hash4",
            created_at=datetime(2025, 1, 1, 14, 0, 0),
        )
        assert result[1] == LyricsCorpus(
            lyrics_corpus_id="corpus-003",
            title="Song 3",
            content_hash="hash3",
            created_at=datetime(2025, 1, 1, 13, 0, 0),
        )
        assert result[2] == LyricsCorpus(
            lyrics_corpus_id="corpus-002",
            title="Song 2",
            content_hash="hash2",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
