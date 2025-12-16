"""Tests for DuckDB MatchRepository implementation."""

from datetime import datetime

from src.domain.models.lyric_token import LyricToken
from src.domain.models.match_result import MatchResult, MatchType
from src.domain.models.match_run import MatchRun
from src.domain.models.reading import Reading
from src.infrastructure.database.duckdb_lyric_token_repository import (
    DuckDBLyricTokenRepository,
)
from src.infrastructure.database.duckdb_match_repository import (
    DuckDBMatchRepository,
)


def test_save_and_find_run(temp_db_with_corpus):
    """Test MatchRepository save and find run operations."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBMatchRepository(str(db_path))

    # Create test match run
    match_run = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="テスト",
        timestamp=datetime.now(),
        config={"max_mora_length": 5},
    )

    # Save match run
    repo.save_run(match_run)

    # Find match run by id
    result = repo.find_run_by_id("run-001")
    assert result is not None
    assert result.input_text == "テスト"
    assert result.config["max_mora_length"] == 5


def test_save_and_find_results(temp_db_with_corpus):
    """Test saving and finding match results."""
    db_path, corpus_id = temp_db_with_corpus

    # Create a token first (for foreign key)
    token_repo = DuckDBLyricTokenRepository(str(db_path))
    token = LyricToken(
        lyrics_corpus_id=corpus_id,
        surface="テスト",
        reading=Reading(raw="テスト"),
        lemma="テスト",
        pos="名詞",
        line_index=0,
        token_index=0,
    )
    token_repo.save(token)

    # Create match run
    repo = DuckDBMatchRepository(str(db_path))
    match_run = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="テスト",
        timestamp=datetime.now(),
        config={"max_mora_length": 5},
    )
    repo.save_run(match_run)

    # Create test match results
    match_results = [
        MatchResult(
            input_token="テスト",
            input_reading="テスト",
            match_type=MatchType.EXACT_SURFACE,
            matched_token_ids=[token.token_id],
            mora_details=[],
        )
    ]

    # Save match results
    repo.save_results("run-001", match_results)

    # Find match results by run_id
    results = repo.find_results_by_run_id("run-001")
    assert len(results) == 1
    assert results[0].input_token == "テスト"
    assert results[0].match_type == MatchType.EXACT_SURFACE


def test_find_runs_by_corpus_id(temp_db_with_corpus):
    """Test finding match runs by corpus ID."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBMatchRepository(str(db_path))

    # Create multiple match runs
    for i in range(3):
        match_run = MatchRun(
            run_id=f"run-00{i}",
            lyrics_corpus_id=corpus_id,
            input_text=f"テスト{i}",
            timestamp=datetime.now(),
            config={"max_mora_length": 5},
        )
        repo.save_run(match_run)

    # Find runs by corpus_id
    results = repo.find_runs_by_lyrics_corpus_id(corpus_id)
    assert len(results) == 3


def test_delete_run(temp_db_with_corpus):
    """Test deleting a match run and its results."""
    db_path, corpus_id = temp_db_with_corpus

    # Create a token first
    token_repo = DuckDBLyricTokenRepository(str(db_path))
    token = LyricToken(
        lyrics_corpus_id=corpus_id,
        surface="テスト",
        reading=Reading(raw="テスト"),
        lemma="テスト",
        pos="名詞",
        line_index=0,
        token_index=0,
    )
    token_repo.save(token)

    # Create match run and results
    repo = DuckDBMatchRepository(str(db_path))
    match_run = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="テスト",
        timestamp=datetime.now(),
        config={"max_mora_length": 5},
    )
    repo.save_run(match_run)

    match_results = [
        MatchResult(
            input_token="テスト",
            input_reading="テスト",
            match_type=MatchType.EXACT_SURFACE,
            matched_token_ids=[token.token_id],
            mora_details=[],
        )
    ]
    repo.save_results("run-001", match_results)

    # Verify they exist
    assert repo.find_run_by_id("run-001") is not None
    assert len(repo.find_results_by_run_id("run-001")) == 1

    # Delete run
    repo.delete_run("run-001")

    # Verify they're gone
    assert repo.find_run_by_id("run-001") is None
    assert len(repo.find_results_by_run_id("run-001")) == 0
