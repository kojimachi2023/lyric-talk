"""Tests for QueryResultsUseCase (Red phase - TDD)."""

from unittest.mock import Mock

from src.application.use_cases.query_results import QueryResultsUseCase
from src.domain.models.match_result import MatchResult
from src.domain.models.match_run import MatchRun


class TestQueryResultsUseCase:
    """Test QueryResultsUseCase."""

    def test_query_results_success(self):
        """Test querying results successfully."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()

        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_123"

        # Mock: match run with results (aggregate)
        match_result1 = Mock(spec=MatchResult)
        match_result1.matched_token_ids = ["token_1", "token_2"]

        match_result2 = Mock(spec=MatchResult)
        match_result2.matched_token_ids = ["token_3"]

        mock_match_run = Mock(spec=MatchRun)
        mock_match_run.results = [match_result1, match_result2]

        match_repo.find_by_id.return_value = mock_match_run

        # Mock: tokens
        token_repo.get_by_id.side_effect = lambda id: Mock(token_id=id, surface=f"surface_{id}")

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is not None
        assert result["match_run"] == mock_match_run
        assert len(result["results"]) == 2

        # Verify repository calls
        match_repo.find_by_id.assert_called_once_with(run_id)
        assert token_repo.get_by_id.call_count == 3  # token_1, token_2, token_3

    def test_query_results_not_found(self):
        """Test querying with run_id not found."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()

        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_not_exists"

        # Mock: run not found
        match_repo.find_by_id.return_value = None

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is None

        # Verify no token lookups
        token_repo.get_by_id.assert_not_called()
