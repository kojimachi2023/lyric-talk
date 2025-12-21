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

    # Create test match run (aggregate)
    match_run = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="テスト",
        timestamp=datetime.now(),
        config={"max_mora_length": 5},
        results=[],  # Empty results
    )

    # Save match run (aggregate)
    repo.save(match_run)

    # Find match run by id
    result = repo.find_by_id("run-001")
    assert result is not None
    assert result.input_text == "テスト"
    assert result.config["max_mora_length"] == 5
    assert result.results == []


def test_save_and_find_run_with_results(temp_db_with_corpus):
    """Test saving and finding match run with results (aggregate)."""
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

    # Create match run with results (aggregate)
    repo = DuckDBMatchRepository(str(db_path))
    match_result = MatchResult(
        input_token="テスト",
        input_reading="テスト",
        match_type=MatchType.EXACT_SURFACE,
        matched_token_ids=[token.token_id],
        mora_details=None,
    )

    match_run = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="テスト",
        timestamp=datetime.now(),
        config={"max_mora_length": 5},
        results=[match_result],
    )

    # Save aggregate
    repo.save(match_run)

    # Find aggregate by id
    result = repo.find_by_id("run-001")
    assert result is not None
    assert len(result.results) == 1
    assert result.results[0].input_token == "テスト"
    assert result.results[0].match_type == MatchType.EXACT_SURFACE


def test_find_by_lyrics_corpus_id(temp_db_with_corpus):
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
            results=[],
        )
        repo.save(match_run)

    # Find runs by corpus_id
    results = repo.find_by_lyrics_corpus_id(corpus_id)
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

    # Create match run with results (aggregate)
    repo = DuckDBMatchRepository(str(db_path))
    match_result = MatchResult(
        input_token="テスト",
        input_reading="テスト",
        match_type=MatchType.EXACT_SURFACE,
        matched_token_ids=[token.token_id],
        mora_details=None,
    )

    match_run = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="テスト",
        timestamp=datetime.now(),
        config={"max_mora_length": 5},
        results=[match_result],
    )
    repo.save(match_run)

    # Verify they exist
    assert repo.find_by_id("run-001") is not None
    assert len(repo.find_by_id("run-001").results) == 1

    # Delete run
    repo.delete("run-001")

    # Verify they're gone
    assert repo.find_by_id("run-001") is None


def test_list_match_runs_empty(temp_db_with_corpus):
    """Test list_match_runs with empty database."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBMatchRepository(str(db_path))

    # Empty database should return empty list
    result = repo.list_match_runs(10)
    assert result == []


def test_list_match_runs_single(temp_db_with_corpus):
    """Test list_match_runs with single match run."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBMatchRepository(str(db_path))

    # Create and save match run
    match_run = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="テスト",
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        config={"max_mora_length": 5},
        results=[],
    )
    repo.save(match_run)

    # List should return the run
    result = repo.list_match_runs(10)
    assert len(result) == 1
    assert result[0].run_id == "run-001"
    assert result[0].input_text == "テスト"


def test_list_match_runs_multiple_ordered(temp_db_with_corpus):
    """Test list_match_runs with multiple runs in descending timestamp order."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBMatchRepository(str(db_path))

    # Create runs with different timestamps
    run1 = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="古いテキスト",
        timestamp=datetime(2025, 1, 1, 10, 0, 0),
        config={},
        results=[],
    )
    run2 = MatchRun(
        run_id="run-002",
        lyrics_corpus_id=corpus_id,
        input_text="新しいテキスト",
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        config={},
        results=[],
    )
    run3 = MatchRun(
        run_id="run-003",
        lyrics_corpus_id=corpus_id,
        input_text="中間テキスト",
        timestamp=datetime(2025, 1, 1, 11, 0, 0),
        config={},
        results=[],
    )

    # Save in random order
    repo.save(run1)
    repo.save(run2)
    repo.save(run3)

    # List should be in descending order (newest first)
    result = repo.list_match_runs(10)
    assert len(result) == 3
    assert result[0].run_id == "run-002"  # Newest
    assert result[0].input_text == "新しいテキスト"
    assert result[1].run_id == "run-003"  # Middle
    assert result[2].run_id == "run-001"  # Oldest


def test_list_match_runs_respects_limit(temp_db_with_corpus):
    """Test list_match_runs respects the limit parameter."""
    db_path, corpus_id = temp_db_with_corpus
    repo = DuckDBMatchRepository(str(db_path))

    # Create 5 runs
    for i in range(5):
        run = MatchRun(
            run_id=f"run-{i:03d}",
            lyrics_corpus_id=corpus_id,
            input_text=f"テキスト{i}",
            timestamp=datetime(2025, 1, 1, 10 + i, 0, 0),
            config={},
            results=[],
        )
        repo.save(run)

    # Request only 3
    result = repo.list_match_runs(3)
    assert len(result) == 3
    # Should get the 3 newest
    assert result[0].run_id == "run-004"
    assert result[1].run_id == "run-003"
    assert result[2].run_id == "run-002"


def test_list_match_runs_includes_results(temp_db_with_corpus):
    """Test list_match_runs includes match results in each run."""
    db_path, corpus_id = temp_db_with_corpus
    token_repo = DuckDBLyricTokenRepository(str(db_path))
    repo = DuckDBMatchRepository(str(db_path))

    # For avoid foreign key constraint, create a token first
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

    # Create run with results
    match_result = MatchResult(
        input_token="テスト",
        input_reading="テスト",
        match_type=MatchType.EXACT_SURFACE,
        matched_token_ids=[token.token_id],
        mora_details=None,
    )
    run = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="テスト",
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        config={},
        results=[match_result],
    )
    repo.save(run)

    # List should include results
    result = repo.list_match_runs(10)
    assert len(result) == 1
    assert len(result[0].results) == 1
    assert result[0].results[0].input_token == "テスト"
