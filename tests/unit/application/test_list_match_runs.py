"""Tests for ListMatchRunsUseCase (TDD - Red phase)."""

from datetime import datetime
from unittest.mock import Mock

from src.application.dtos.cli_summaries import MatchRunSummaryDto
from src.application.use_cases.list_match_runs import ListMatchRunsUseCase
from src.domain.models.match_result import MatchResult
from src.domain.models.match_run import MatchRun


class TestListMatchRunsUseCase:
    """Test ListMatchRunsUseCase."""

    def test_list_empty_runs(self):
        """Test listing when no match runs exist."""
        # Arrange
        uow = Mock()
        uow.match_repository = Mock()
        use_case = ListMatchRunsUseCase(unit_of_work=uow)

        # Mock: no runs exist
        uow.match_repository.list_match_runs.return_value = []

        # Act
        result = use_case.execute(limit=10)

        # Assert
        assert result == []
        uow.match_repository.list_match_runs.assert_called_once_with(10)

    def test_list_single_run(self):
        """Test listing with a single match run."""
        # Arrange
        uow = Mock()
        uow.match_repository = Mock()
        use_case = ListMatchRunsUseCase(unit_of_work=uow)

        # Mock data
        run = MatchRun(
            run_id="run_1",
            lyrics_corpus_id="corpus_1",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            input_text="テストテキスト",
            config={"max_mora_length": 10},
            results=[
                MatchResult(
                    input_token="テスト",
                    input_reading="テスト",
                    input_token_index=0,
                    match_type="exact_surface",
                    matched_token_ids=["token_1"],
                )
            ],
        )
        uow.match_repository.list_match_runs.return_value = [run]

        # Act
        result = use_case.execute(limit=10)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], MatchRunSummaryDto)
        assert result[0].run_id == "run_1"
        assert result[0].lyrics_corpus_id == "corpus_1"
        assert result[0].timestamp == datetime(2025, 1, 1, 12, 0, 0)
        assert result[0].input_text == "テストテキスト"
        assert result[0].results_count == 1

        uow.match_repository.list_match_runs.assert_called_once_with(10)

    def test_list_multiple_runs_ordered(self):
        """Test listing multiple runs in correct order (most recent first)."""
        # Arrange
        uow = Mock()
        uow.match_repository = Mock()
        use_case = ListMatchRunsUseCase(unit_of_work=uow)

        # Mock data: multiple runs with different timestamps
        run1 = MatchRun(
            run_id="run_1",
            lyrics_corpus_id="corpus_1",
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            input_text="古いテキスト",
            config={},
            results=[],
        )
        run2 = MatchRun(
            run_id="run_2",
            lyrics_corpus_id="corpus_1",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            input_text="新しいテキスト",
            config={},
            results=[
                MatchResult(
                    input_token="新しい",
                    input_reading="アタラシイ",
                    input_token_index=0,
                    match_type="exact_surface",
                    matched_token_ids=["token_1"],
                ),
                MatchResult(
                    input_token="テキスト",
                    input_reading="テキスト",
                    input_token_index=1,
                    match_type="mora_combination",
                    matched_token_ids=["token_2", "token_3"],
                ),
            ],
        )
        run3 = MatchRun(
            run_id="run_3",
            lyrics_corpus_id="corpus_2",
            timestamp=datetime(2025, 1, 1, 11, 0, 0),
            input_text="中間テキスト",
            config={},
            results=[
                MatchResult(
                    input_token="中間",
                    input_reading="チュウカン",
                    input_token_index=0,
                    match_type="exact_surface",
                    matched_token_ids=["token_4"],
                )
            ],
        )

        # Repository returns already sorted (most recent first)
        uow.match_repository.list_match_runs.return_value = [run2, run3, run1]

        # Act
        result = use_case.execute(limit=10)

        # Assert
        assert len(result) == 3
        # Check order is preserved from repository
        assert result[0].run_id == "run_2"
        assert result[0].results_count == 2
        assert result[1].run_id == "run_3"
        assert result[1].results_count == 1
        assert result[2].run_id == "run_1"
        assert result[2].results_count == 0

        uow.match_repository.list_match_runs.assert_called_once_with(10)

    def test_list_respects_limit(self):
        """Test that the limit parameter is passed correctly to repository."""
        # Arrange
        uow = Mock()
        uow.match_repository = Mock()
        use_case = ListMatchRunsUseCase(unit_of_work=uow)
        uow.match_repository.list_match_runs.return_value = []

        # Act
        use_case.execute(limit=5)

        # Assert
        uow.match_repository.list_match_runs.assert_called_once_with(5)

    def test_list_with_no_results(self):
        """Test listing runs that have no match results."""
        # Arrange
        uow = Mock()
        uow.match_repository = Mock()
        use_case = ListMatchRunsUseCase(unit_of_work=uow)

        # Mock data: run with empty results
        run = MatchRun(
            run_id="run_empty",
            lyrics_corpus_id="corpus_1",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            input_text="結果なし",
            config={},
            results=[],
        )
        uow.match_repository.list_match_runs.return_value = [run]

        # Act
        result = use_case.execute(limit=10)

        # Assert
        assert len(result) == 1
        assert result[0].results_count == 0
