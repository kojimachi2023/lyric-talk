"""Tests for DuckDB LyricTokenRepository implementation."""

from datetime import datetime

from src.domain.models.lyric_token import LyricToken
from src.domain.models.lyrics_corpus import LyricsCorpus
from src.domain.models.reading import Reading
from src.infrastructure.database.duckdb_unit_of_work import DuckDBUnitOfWork


def test_save_and_find(unit_of_work_with_corpus):
    """Test LyricTokenRepository save and find operations."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.lyric_token_repository.save(token)

    # Find by surface
    results = uow.lyric_token_repository.find_by_surface("東京", corpus_id)
    assert len(results) == 1
    assert results[0].surface == "東京"

    # Find by reading
    results = uow.lyric_token_repository.find_by_reading("トウキョウ", corpus_id)
    assert len(results) == 1
    assert results[0].surface == "東京"

    # Find by token_id
    token_id = token.token_id
    result = uow.lyric_token_repository.find_by_token_id(token_id)
    assert result is not None
    assert result.surface == "東京"


def test_save_many(unit_of_work_with_corpus):
    """Test LyricTokenRepository save_many operation."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.lyric_token_repository.save_many(tokens)

    # Verify saved
    results = uow.lyric_token_repository.find_by_surface("東京", corpus_id)
    assert len(results) == 1
    results = uow.lyric_token_repository.find_by_surface("へ", corpus_id)
    assert len(results) == 1


def test_find_by_mora(unit_of_work_with_corpus):
    """Test LyricTokenRepository find_by_mora operation."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.lyric_token_repository.save(token)

    # Find by mora
    results = uow.lyric_token_repository.find_by_mora("ト", corpus_id)
    assert len(results) >= 1
    assert any(r.surface == "東京" for r in results)


def test_find_by_token_ids(unit_of_work_with_corpus):
    """Test finding multiple tokens by IDs."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.lyric_token_repository.save_many(tokens)

    # Find by multiple IDs
    token_ids = [t.token_id for t in tokens]
    results = uow.lyric_token_repository.find_by_token_ids(token_ids)
    assert len(results) == 2


def test_has_mora(unit_of_work_with_corpus):
    """Test checking if corpus has a specific mora."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.lyric_token_repository.save(token)

    # Check if mora exists
    assert uow.lyric_token_repository.has_mora("ト", corpus_id) is True
    assert uow.lyric_token_repository.has_mora("ザ", corpus_id) is False


def test_repositories_isolation(temp_db):
    """Test that repositories work with different corpus_ids."""
    # Create two corpora
    with DuckDBUnitOfWork(str(temp_db)) as uow:
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
        uow.lyrics_repository.save(corpus1)
        uow.lyrics_repository.save(corpus2)

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

        uow.lyric_token_repository.save(token1)
        uow.lyric_token_repository.save(token2)
        uow.commit()

    # Find by surface should only return tokens from specified corpus
    with DuckDBUnitOfWork(str(temp_db)) as uow:
        results = uow.lyric_token_repository.find_by_surface("東京", "corpus-001")
        assert len(results) == 1
        assert results[0] == token1

        results = uow.lyric_token_repository.find_by_surface("東京", "corpus-002")
        assert len(results) == 1
        assert results[0] == token2


def test_count_by_lyrics_corpus_id_empty(unit_of_work_with_corpus):
    """Test count_by_lyrics_corpus_id with no tokens."""
    uow, corpus_id = unit_of_work_with_corpus

    # Empty corpus should have count 0
    count = uow.lyric_token_repository.count_by_lyrics_corpus_id(corpus_id)
    assert count == 0


def test_count_by_lyrics_corpus_id_single(unit_of_work_with_corpus):
    """Test count_by_lyrics_corpus_id with single token."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.lyric_token_repository.save(token)

    # Count should be 1
    count = uow.lyric_token_repository.count_by_lyrics_corpus_id(corpus_id)
    assert count == 1


def test_count_by_lyrics_corpus_id_multiple(unit_of_work_with_corpus):
    """Test count_by_lyrics_corpus_id with multiple tokens."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.lyric_token_repository.save_many(tokens)

    # Count should be 3
    count = uow.lyric_token_repository.count_by_lyrics_corpus_id(corpus_id)
    assert count == 3


def test_list_by_lyrics_corpus_id_empty(unit_of_work_with_corpus):
    """Test list_by_lyrics_corpus_id with no tokens."""
    uow, corpus_id = unit_of_work_with_corpus

    # Empty corpus should return empty list
    tokens = uow.lyric_token_repository.list_by_lyrics_corpus_id(corpus_id, limit=10)
    assert tokens == []


def test_list_by_lyrics_corpus_id_ordered(unit_of_work_with_corpus):
    """Test list_by_lyrics_corpus_id returns tokens in correct order."""
    uow, corpus_id = unit_of_work_with_corpus

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
        uow.lyric_token_repository.save(token)

    # List should be in line_index, token_index order
    result = uow.lyric_token_repository.list_by_lyrics_corpus_id(corpus_id, limit=10)
    assert len(result) == 3
    assert result[0].surface == "東京"  # line_index=0, token_index=0
    assert result[1].surface == "へ"  # line_index=0, token_index=1
    assert result[2].surface == "行く"  # line_index=0, token_index=2


def test_list_by_lyrics_corpus_id_respects_limit(unit_of_work_with_corpus):
    """Test list_by_lyrics_corpus_id respects limit parameter."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.lyric_token_repository.save_many(tokens)

    # Request only 3
    result = uow.lyric_token_repository.list_by_lyrics_corpus_id(corpus_id, limit=3)
    assert len(result) == 3
    # Should get first 3 in order
    assert result[0].surface == "token0"
    assert result[1].surface == "token1"
    assert result[2].surface == "token2"
