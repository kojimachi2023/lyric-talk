"""Tests for QueryResultsUseCase (updated for DTO refactoring)."""

from datetime import datetime
from unittest.mock import Mock

from src.application.dtos.query_results_dto import QueryResultsDto
from src.application.use_cases.query_results import QueryResultsUseCase
from src.domain.models.lyric_token import LyricToken
from src.domain.models.match_result import MatchResult, MatchType, MoraMatchDetail
from src.domain.models.match_run import MatchRun
from src.domain.models.reading import Reading


class TestQueryResultsUseCase:
    """Test QueryResultsUseCase (updated for DTO)."""

    def test_query_results_not_found(self):
        """Test querying results when run is not found."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()

        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "non_existent_run"
        match_repo.find_by_id.return_value = None

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is None
        match_repo.find_by_id.assert_called_once_with(run_id)

    def test_query_results_success_exact_match(self):
        """Test querying results successfully with exact match types (returns DTO)."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()

        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_123"

        # Mock: match run with results (aggregate) - exact match type
        match_result1 = MatchResult(
            input_token="hello",
            input_reading="ハロー",
            match_type=MatchType.EXACT_SURFACE,
            matched_token_ids=["token_1", "token_2"],
            mora_details=None,
        )

        match_result2 = MatchResult(
            input_token="world",
            input_reading="ワールド",
            match_type=MatchType.EXACT_READING,
            matched_token_ids=["token_3"],
            mora_details=None,
        )

        mock_match_run = MatchRun(
            run_id=run_id,
            lyrics_corpus_id="corpus_1",
            timestamp=datetime(2025, 12, 21, 12, 0, 0),
            input_text="hello world",
            config={},
            results=[match_result1, match_result2],
        )

        match_repo.find_by_id.return_value = mock_match_run

        # Mock: tokens
        token1 = LyricToken(
            lyrics_corpus_id="corpus_1",
            surface="hello",
            reading=Reading(raw="ハロー"),
            lemma="hello",
            pos="noun",
            line_index=0,
            token_index=0,
        )
        token2 = LyricToken(
            lyrics_corpus_id="corpus_1",
            surface="",
            reading=Reading(raw=""),
            lemma="",
            pos="noun",
            line_index=0,
            token_index=1,
        )
        token3 = LyricToken(
            lyrics_corpus_id="corpus_1",
            surface="world",
            reading=Reading(raw="ワールド"),
            lemma="world",
            pos="noun",
            line_index=0,
            token_index=2,
        )

        token_repo.get_by_id.side_effect = lambda tid: (
            {"token_1": token1, "token_2": token2, "token_3": token3}.get(tid)
        )

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is not None
        assert isinstance(result, QueryResultsDto)
        assert result.match_run.run_id == run_id
        assert len(result.items) == 2

        # Verify repository calls
        match_repo.find_by_id.assert_called_once_with(run_id)
        assert token_repo.get_by_id.call_count == 3  # token_1, token_2, token_3

    def test_query_results_success_mora_combination(self):
        """Test querying results successfully with mora combination match type (returns DTO)."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()

        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_456"

        # Mock: match run with results (aggregate) - mora combination
        mora_detail1 = MoraMatchDetail(mora="ト", source_token_id="token_a", mora_index=0)
        mora_detail2 = MoraMatchDetail(mora="キョ", source_token_id="token_b", mora_index=1)
        mora_detail3 = MoraMatchDetail(
            mora="ト", source_token_id="token_a", mora_index=0
        )  # Duplicate to test deduplication

        match_result = MatchResult(
            input_token="トキョ",
            input_reading="トキョ",
            match_type=MatchType.MORA_COMBINATION,
            matched_token_ids=[],
            mora_details=[mora_detail1, mora_detail2, mora_detail3],
        )

        mock_match_run = MatchRun(
            run_id=run_id,
            lyrics_corpus_id="corpus_2",
            timestamp=datetime(2025, 12, 21, 12, 0, 0),
            input_text="トキョ",
            config={},
            results=[match_result],
        )

        match_repo.find_by_id.return_value = mock_match_run

        # Mock: tokens
        token_a = LyricToken(
            lyrics_corpus_id="corpus_2",
            surface="東",
            reading=Reading(raw="トウ"),
            lemma="東",
            pos="noun",
            line_index=0,
            token_index=0,
        )
        token_b = LyricToken(
            lyrics_corpus_id="corpus_2",
            surface="京都",
            reading=Reading(raw="キョウト"),
            lemma="京都",
            pos="noun",
            line_index=0,
            token_index=1,
        )

        token_repo.get_by_id.side_effect = lambda tid: (
            {"token_a": token_a, "token_b": token_b}.get(tid)
        )

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is not None
        assert isinstance(result, QueryResultsDto)
        assert len(result.items) == 1
        # Should only resolve 2 unique tokens (token_a appears twice but deduplicated)
        assert len(result.items[0].chosen_lyrics_tokens) == 2

        # Verify repository calls - should be called 2 times (deduplicated)
        assert token_repo.get_by_id.call_count == 2  # token_a and token_b
