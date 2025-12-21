"""Tests for DuckDB LyricTokenRepository implementation."""

from datetime import datetime

from src.domain.models.lyric_token import LyricToken
from src.domain.models.lyrics_corpus import LyricsCorpus
from src.domain.models.reading import Reading
from src.infrastructure.database.duckdb_lyric_token_repository import (
    DuckDBLyricTokenRepository,
)
from src.infrastructure.database.duckdb_lyrics_repository import (
    DuckDBLyricsRepository,
)


def test_save_and_find(temp_db_with_corpus):
    """Test LyricTokenRepository save and find operations."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Create test token
    token = LyricToken(
        lyrics_corpus_id=corpus_id,
        surface="東京",
        reading=Reading(raw="トウキョウ"),
        lemma="東京",
        pos="名詞",
        line_index=0,
        token_index=0,
    )

    # Save token
    repo.save(token)

    # Find by surface
    results = repo.find_by_surface("東京", corpus_id)
    assert len(results) == 1
    assert results[0].surface == "東京"

    # Find by reading
    results = repo.find_by_reading("トウキョウ", corpus_id)
    assert len(results) == 1
    assert results[0].surface == "東京"

    # Find by token_id
    token_id = token.token_id
    result = repo.find_by_token_id(token_id)
    assert result is not None
    assert result.surface == "東京"


def test_save_many(temp_db_with_corpus):
    """Test LyricTokenRepository save_many operation."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Create test tokens
    tokens = [
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="東京",
            reading=Reading(raw="トウキョウ"),
            lemma="東京",
            pos="名詞",
            line_index=0,
            token_index=0,
        ),
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="へ",
            reading=Reading(raw="エ"),
            lemma="へ",
            pos="助詞",
            line_index=0,
            token_index=1,
        ),
    ]

    # Save multiple tokens
    repo.save_many(tokens)

    # Verify saved
    results = repo.find_by_surface("東京", corpus_id)
    assert len(results) == 1
    results = repo.find_by_surface("へ", corpus_id)
    assert len(results) == 1


def test_find_by_mora(temp_db_with_corpus):
    """Test LyricTokenRepository find_by_mora operation."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Create test token
    token = LyricToken(
        lyrics_corpus_id=corpus_id,
        surface="東京",
        reading=Reading(raw="トウキョウ"),
        lemma="東京",
        pos="名詞",
        line_index=0,
        token_index=0,
    )
    repo.save(token)

    # Find by mora
    results = repo.find_by_mora("ト", corpus_id)
    assert len(results) >= 1
    assert any(r.surface == "東京" for r in results)


def test_find_by_token_ids(temp_db_with_corpus):
    """Test finding multiple tokens by IDs."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Create test tokens
    tokens = [
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="東京",
            reading=Reading(raw="トウキョウ"),
            lemma="東京",
            pos="名詞",
            line_index=0,
            token_index=0,
        ),
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="へ",
            reading=Reading(raw="エ"),
            lemma="へ",
            pos="助詞",
            line_index=0,
            token_index=1,
        ),
    ]
    repo.save_many(tokens)

    # Find by multiple IDs
    token_ids = [t.token_id for t in tokens]
    results = repo.find_by_token_ids(token_ids)
    assert len(results) == 2


def test_has_mora(temp_db_with_corpus):
    """Test checking if corpus has a specific mora."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Create test token
    token = LyricToken(
        lyrics_corpus_id=corpus_id,
        surface="東京",
        reading=Reading(raw="トウキョウ"),
        lemma="東京",
        pos="名詞",
        line_index=0,
        token_index=0,
    )
    repo.save(token)

    # Check if mora exists
    assert repo.has_mora("ト", corpus_id) is True
    assert repo.has_mora("ザ", corpus_id) is False


def test_repositories_isolation(temp_db):
    """Test that repositories work with different corpus_ids."""
    # Create two corpora
    lyrics_repo = DuckDBLyricsRepository(str(temp_db))
    corpus1 = LyricsCorpus(
        lyrics_corpus_id="corpus-001",
        content_hash="hash1",
        title="Test1",
        created_at=datetime.now(),
    )
    corpus2 = LyricsCorpus(
        lyrics_corpus_id="corpus-002",
        content_hash="hash2",
        title="Test2",
        created_at=datetime.now(),
    )
    lyrics_repo.save(corpus1)
    lyrics_repo.save(corpus2)

    repo = DuckDBLyricTokenRepository(str(temp_db))

    # Create tokens for different corpora
    token1 = LyricToken(
        lyrics_corpus_id="corpus-001",
        surface="東京",
        reading=Reading(raw="トウキョウ"),
        lemma="東京",
        pos="名詞",
        line_index=0,
        token_index=0,
    )
    token2 = LyricToken(
        lyrics_corpus_id="corpus-002",
        surface="東京",
        reading=Reading(raw="トウキョウ"),
        lemma="東京",
        pos="名詞",
        line_index=0,
        token_index=0,
    )

    repo.save(token1)
    repo.save(token2)

    # Find by surface should only return tokens from specified corpus
    results = repo.find_by_surface("東京", "corpus-001")
    assert len(results) == 1
    assert results[0].lyrics_corpus_id == "corpus-001"

    results = repo.find_by_surface("東京", "corpus-002")
    assert len(results) == 1
    assert results[0].lyrics_corpus_id == "corpus-002"


def test_count_by_lyrics_corpus_id_empty(temp_db_with_corpus):
    """Test count_by_lyrics_corpus_id with no tokens."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Empty corpus should have count 0
    count = repo.count_by_lyrics_corpus_id(corpus_id)
    assert count == 0


def test_count_by_lyrics_corpus_id_single(temp_db_with_corpus):
    """Test count_by_lyrics_corpus_id with single token."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Create and save token
    token = LyricToken(
        lyrics_corpus_id=corpus_id,
        surface="東京",
        reading=Reading(raw="トウキョウ"),
        lemma="東京",
        pos="名詞",
        line_index=0,
        token_index=0,
    )
    repo.save(token)

    # Count should be 1
    count = repo.count_by_lyrics_corpus_id(corpus_id)
    assert count == 1


def test_count_by_lyrics_corpus_id_multiple(temp_db_with_corpus):
    """Test count_by_lyrics_corpus_id with multiple tokens."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Create and save multiple tokens
    tokens = [
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="東京",
            reading=Reading(raw="トウキョウ"),
            lemma="東京",
            pos="名詞",
            line_index=0,
            token_index=0,
        ),
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="へ",
            reading=Reading(raw="エ"),
            lemma="へ",
            pos="助詞",
            line_index=0,
            token_index=1,
        ),
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="行く",
            reading=Reading(raw="イク"),
            lemma="行く",
            pos="動詞",
            line_index=0,
            token_index=2,
        ),
    ]
    repo.save_many(tokens)

    # Count should be 3
    count = repo.count_by_lyrics_corpus_id(corpus_id)
    assert count == 3


def test_list_by_lyrics_corpus_id_empty(temp_db_with_corpus):
    """Test list_by_lyrics_corpus_id with no tokens."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Empty corpus should return empty list
    tokens = repo.list_by_lyrics_corpus_id(corpus_id, limit=10)
    assert tokens == []


def test_list_by_lyrics_corpus_id_ordered(temp_db_with_corpus):
    """Test list_by_lyrics_corpus_id returns tokens in correct order."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Create tokens in random order
    tokens = [
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="へ",
            reading=Reading(raw="エ"),
            lemma="へ",
            pos="助詞",
            line_index=0,
            token_index=1,
        ),
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="東京",
            reading=Reading(raw="トウキョウ"),
            lemma="東京",
            pos="名詞",
            line_index=0,
            token_index=0,
        ),
        LyricToken(
            lyrics_corpus_id=corpus_id,
            surface="行く",
            reading=Reading(raw="イク"),
            lemma="行く",
            pos="動詞",
            line_index=0,
            token_index=2,
        ),
    ]
    # Save in random order
    for token in tokens:
        repo.save(token)

    # List should be in line_index, token_index order
    result = repo.list_by_lyrics_corpus_id(corpus_id, limit=10)
    assert len(result) == 3
    assert result[0].surface == "東京"  # line_index=0, token_index=0
    assert result[1].surface == "へ"  # line_index=0, token_index=1
    assert result[2].surface == "行く"  # line_index=0, token_index=2


def test_list_by_lyrics_corpus_id_respects_limit(temp_db_with_corpus):
    """Test list_by_lyrics_corpus_id respects limit parameter."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBLyricTokenRepository(str(db_path))

    # Create 5 tokens
    tokens = []
    for i in range(5):
        tokens.append(
            LyricToken(
                lyrics_corpus_id=corpus_id,
                surface=f"token{i}",
                reading=Reading(raw="トークン"),
                lemma=f"token{i}",
                pos="名詞",
                line_index=0,
                token_index=i,
            )
        )
    repo.save_many(tokens)

    # Request only 3
    result = repo.list_by_lyrics_corpus_id(corpus_id, limit=3)
    assert len(result) == 3
    # Should get first 3 in order
    assert result[0].surface == "token0"
    assert result[1].surface == "token1"
    assert result[2].surface == "token2"
