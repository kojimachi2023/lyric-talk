"""Tests for QueryResultsUseCase (Red phase - TDD)."""

from unittest.mock import Mock

from src.application.use_cases.query_results import QueryResultsUseCase
from src.domain.models.match_result import MatchResult, MatchType, MoraMatchDetail
from src.domain.models.match_run import MatchRun


class TestQueryResultsUseCase:
    """Test QueryResultsUseCase."""

    def test_query_results_success_exact_match(self):
        """Test querying results successfully with exact match types."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()

        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_123"

        # Mock: match run with results (aggregate) - exact match type
        match_result1 = Mock(spec=MatchResult)
        match_result1.match_type = MatchType.EXACT_SURFACE
        match_result1.matched_token_ids = ["token_1", "token_2"]
        match_result1.mora_details = None

        match_result2 = Mock(spec=MatchResult)
        match_result2.match_type = MatchType.EXACT_READING
        match_result2.matched_token_ids = ["token_3"]
        match_result2.mora_details = None

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

    def test_query_results_success_mora_combination(self):
        """Test querying results successfully with mora combination match type."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()

        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_456"

        # Mock: match run with results (aggregate) - mora combination
        mora_detail1 = Mock(spec=MoraMatchDetail)
        mora_detail1.source_token_id = "token_a"
        mora_detail2 = Mock(spec=MoraMatchDetail)
        mora_detail2.source_token_id = "token_b"
        mora_detail3 = Mock(spec=MoraMatchDetail)
        mora_detail3.source_token_id = "token_a"  # Duplicate to test deduplication

        match_result = Mock(spec=MatchResult)
        match_result.match_type = MatchType.MORA_COMBINATION
        match_result.matched_token_ids = []  # Empty for mora combination
        match_result.mora_details = [mora_detail1, mora_detail2, mora_detail3]

        mock_match_run = Mock(spec=MatchRun)
        mock_match_run.results = [match_result]

        match_repo.find_by_id.return_value = mock_match_run

        # Mock: tokens
        token_repo.get_by_id.side_effect = lambda id: Mock(token_id=id, surface=f"surface_{id}")

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is not None
        assert len(result["results"]) == 1
        # Should only resolve 2 unique tokens (token_a appears twice but deduplicated)
        assert len(result["results"][0]["resolved_tokens"]) == 2

        # Verify repository calls - should be called 2 times (deduplicated)
        assert token_repo.get_by_id.call_count == 2

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
