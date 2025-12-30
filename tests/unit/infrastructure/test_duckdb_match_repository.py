"""Tests for DuckDB MatchRepository implementation."""

from datetime import datetime

from src.domain.models.lyric_token import LyricToken
from src.domain.models.match_result import MatchResult, MatchType
from src.domain.models.match_run import MatchRun
from src.domain.models.reading import Reading


def test_save_and_find_run(unit_of_work_with_corpus):
    """Test MatchRepository save and find run operations."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.match_repository.save(match_run)

    # Find match run by id
    result = uow.match_repository.find_by_id("run-001")
    assert result is not None
    assert result == match_run


def test_save_and_find_run_with_results(unit_of_work_with_corpus):
    """Test saving and finding match run with results (aggregate)."""
    uow, corpus_id = unit_of_work_with_corpus

    # Create a token first (for foreign key)
    token = LyricToken(
        lyrics_corpus_id=corpus_id,
        surface="テスト",
        reading=Reading(raw="テスト"),
        lemma="テスト",
        pos="名詞",
        line_index=0,
        token_index=0,
    )
    uow.lyric_token_repository.save(token)

    # Create match run with results (aggregate)
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
    uow.match_repository.save(match_run)

    # Find aggregate by id
    result = uow.match_repository.find_by_id("run-001")
    assert result is not None
    assert len(result.results) == 1
    assert result == match_run


def test_find_by_lyrics_corpus_id(unit_of_work_with_corpus):
    """Test finding match runs by corpus ID."""
    uow, corpus_id = unit_of_work_with_corpus

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
        uow.match_repository.save(match_run)

    # Find runs by corpus_id
    results = uow.match_repository.find_by_lyrics_corpus_id(corpus_id)
    assert len(results) == 3


def test_delete_run(unit_of_work_with_corpus):
    """Test deleting a match run and its results."""
    uow, corpus_id = unit_of_work_with_corpus

    # Create a token first
    token = LyricToken(
        lyrics_corpus_id=corpus_id,
        surface="テスト",
        reading=Reading(raw="テスト"),
        lemma="テスト",
        pos="名詞",
        line_index=0,
        token_index=0,
    )
    uow.lyric_token_repository.save(token)

    # Create match run with results (aggregate)
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
    uow.match_repository.save(match_run)

    # Verify they exist
    assert uow.match_repository.find_by_id("run-001") is not None
    assert len(uow.match_repository.find_by_id("run-001").results) == 1

    # Delete run
    uow.match_repository.delete("run-001")

    # Verify they're gone
    assert uow.match_repository.find_by_id("run-001") is None


def test_list_match_runs_empty(unit_of_work_with_corpus):
    """Test list_match_runs with empty database."""
    uow, corpus_id = unit_of_work_with_corpus

    # Empty database should return empty list
    result = uow.match_repository.list_match_runs(10)
    assert result == []


def test_list_match_runs_single(unit_of_work_with_corpus):
    """Test list_match_runs with single match run."""
    uow, corpus_id = unit_of_work_with_corpus

    # Create and save match run
    match_run = MatchRun(
        run_id="run-001",
        lyrics_corpus_id=corpus_id,
        input_text="テスト",
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        config={"max_mora_length": 5},
        results=[],
    )
    uow.match_repository.save(match_run)

    # List should return the run
    result = uow.match_repository.list_match_runs(10)
    assert len(result) == 1
    assert result[0] == match_run


def test_list_match_runs_multiple_ordered(unit_of_work_with_corpus):
    """Test list_match_runs with multiple runs in descending timestamp order."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.match_repository.save(run1)
    uow.match_repository.save(run2)
    uow.match_repository.save(run3)

    # List should be in descending order (newest first)
    result = uow.match_repository.list_match_runs(10)
    assert len(result) == 3
    assert result[0] == run2  # Newest
    assert result[1] == run3  # Middle
    assert result[2] == run1  # Oldest


def test_list_match_runs_respects_limit(unit_of_work_with_corpus):
    """Test list_match_runs respects the limit parameter."""
    uow, corpus_id = unit_of_work_with_corpus

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
        uow.match_repository.save(run)

    # Request only 3
    result = uow.match_repository.list_match_runs(3)
    assert len(result) == 3
    # Should get the 3 newest
    assert result[0].run_id == "run-004"
    assert result[1].run_id == "run-003"
    assert result[2].run_id == "run-002"


def test_list_match_runs_includes_results(unit_of_work_with_corpus):
    """Test list_match_runs includes match results in each run."""
    uow, corpus_id = unit_of_work_with_corpus

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
    uow.lyric_token_repository.save(token)

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
    uow.match_repository.save(run)

    # List should include results
    result = uow.match_repository.list_match_runs(10)
    assert len(result) == 1
    assert len(result[0].results) == 1
    assert result[0].results[0] == match_result
