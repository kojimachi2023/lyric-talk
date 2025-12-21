"""Tests for QueryResultsDto and refactored QueryResultsUseCase (TDD - Red phase)."""

from datetime import datetime
from unittest.mock import Mock

from src.application.dtos.query_results_dto import QueryResultsDto
from src.application.use_cases.query_results import QueryResultsUseCase
from src.domain.models.lyric_token import LyricToken
from src.domain.models.match_result import MatchResult, MatchType, MoraMatchDetail
from src.domain.models.match_run import MatchRun
from src.domain.models.reading import Reading


class TestQueryResultsDtoRefactor:
    """Test QueryResultsUseCase refactored to return QueryResultsDto."""

    def test_execute_returns_none_when_run_not_found(self):
        """Test that execute returns None when run_id is not found."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()
        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "nonexistent_run"
        match_repo.find_by_id.return_value = None

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is None
        match_repo.find_by_id.assert_called_once_with(run_id)

    def test_execute_returns_dto_for_exact_surface_match(self):
        """Test that execute returns QueryResultsDto for EXACT_SURFACE match type."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()
        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_exact_surface"
        corpus_id = "corpus_1"
        timestamp = datetime(2025, 12, 21, 12, 0, 0)
        input_text = "こんにちは"

        # Mock match result with exact surface match
        match_result = MatchResult(
            input_token="こんにちは",
            input_reading="コンニチハ",
            match_type=MatchType.EXACT_SURFACE,
            matched_token_ids=["token_1", "token_2"],
            mora_details=None,
        )

        match_run = MatchRun(
            run_id=run_id,
            lyrics_corpus_id=corpus_id,
            input_text=input_text,
            timestamp=timestamp,
            config={},
            results=[match_result],
        )

        match_repo.find_by_id.return_value = match_run

        # Mock tokens
        token1 = LyricToken(
            token_id="token_1",
            lyrics_corpus_id=corpus_id,
            line_index=0,
            token_index=0,
            surface="こんにち",
            reading=Reading(raw="コンニチ"),
            lemma="こんにち",
            pos="名詞",
        )
        token2 = LyricToken(
            token_id="token_2",
            lyrics_corpus_id=corpus_id,
            line_index=0,
            token_index=1,
            surface="は",
            reading=Reading(raw="ハ"),
            lemma="は",
            pos="助詞",
        )

        token_repo.get_by_id.side_effect = lambda tid: (
            {"token_1": token1, "token_2": token2}.get(tid)
        )

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is not None
        assert isinstance(result, QueryResultsDto)
        assert result.match_run.run_id == run_id
        assert result.match_run.lyrics_corpus_id == corpus_id
        assert result.match_run.input_text == input_text
        assert len(result.items) == 1
        assert result.items[0].match_type == MatchType.EXACT_SURFACE
        assert len(result.items[0].chosen_lyrics_tokens) == 2
        assert result.summary.reconstructed_surface == "こんにちは"
        assert result.summary.reconstructed_reading == "コンニチハ"
        assert result.summary.stats.exact_surface_count == 1

    def test_execute_returns_dto_for_exact_reading_match(self):
        """Test that execute returns QueryResultsDto for EXACT_READING match type."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()
        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_exact_reading"
        corpus_id = "corpus_1"
        timestamp = datetime(2025, 12, 21, 12, 0, 0)
        input_text = "おはよう"

        # Mock match result with exact reading match
        match_result = MatchResult(
            input_token="おはよう",
            input_reading="オハヨウ",
            match_type=MatchType.EXACT_READING,
            matched_token_ids=["token_3"],
            mora_details=None,
        )

        match_run = MatchRun(
            run_id=run_id,
            lyrics_corpus_id=corpus_id,
            input_text=input_text,
            timestamp=timestamp,
            config={},
            results=[match_result],
        )

        match_repo.find_by_id.return_value = match_run

        # Mock token
        token3 = LyricToken(
            token_id="token_3",
            lyrics_corpus_id=corpus_id,
            line_index=0,
            token_index=0,
            surface="御早う",
            reading=Reading(raw="オハヨウ"),
            lemma="お早う",
            pos="感動詞",
        )

        token_repo.get_by_id.return_value = token3

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is not None
        assert isinstance(result, QueryResultsDto)
        assert result.items[0].match_type == MatchType.EXACT_READING
        assert result.summary.reconstructed_surface == "御早う"
        assert result.summary.reconstructed_reading == "オハヨウ"
        assert result.summary.stats.exact_reading_count == 1

    def test_execute_returns_dto_for_mora_combination_match(self):
        """Test that execute returns QueryResultsDto for MORA_COMBINATION with mora trace."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()
        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_mora"
        corpus_id = "corpus_1"
        timestamp = datetime(2025, 12, 21, 12, 0, 0)
        input_text = "トキョ"

        # Mock match result with mora combination
        mora_detail1 = MoraMatchDetail(mora="ト", source_token_id="token_a", mora_index=0)
        mora_detail2 = MoraMatchDetail(mora="キョ", source_token_id="token_b", mora_index=1)

        match_result = MatchResult(
            input_token="トキョ",
            input_reading="トキョ",
            match_type=MatchType.MORA_COMBINATION,
            matched_token_ids=[],
            mora_details=[mora_detail1, mora_detail2],
        )

        match_run = MatchRun(
            run_id=run_id,
            lyrics_corpus_id=corpus_id,
            input_text=input_text,
            timestamp=timestamp,
            config={},
            results=[match_result],
        )

        match_repo.find_by_id.return_value = match_run

        # Mock tokens
        token_a = LyricToken(
            token_id="token_a",
            lyrics_corpus_id=corpus_id,
            line_index=0,
            token_index=0,
            surface="東",
            reading=Reading(raw="トウ"),
            lemma="東",
            pos="名詞",
        )
        token_b = LyricToken(
            token_id="token_b",
            lyrics_corpus_id=corpus_id,
            line_index=0,
            token_index=1,
            surface="京都",
            reading=Reading(raw="キョウト"),
            lemma="京都",
            pos="名詞",
        )

        token_repo.get_by_id.side_effect = lambda tid: (
            {"token_a": token_a, "token_b": token_b}.get(tid)
        )

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is not None
        assert isinstance(result, QueryResultsDto)
        assert result.items[0].match_type == MatchType.MORA_COMBINATION
        assert result.items[0].mora_trace is not None
        assert len(result.items[0].mora_trace.items) == 2
        assert result.summary.reconstructed_reading == "トキョ"
        assert result.summary.stats.mora_combination_count == 1

    def test_execute_handles_multiple_results_with_mixed_match_types(self):
        """Test that execute handles multiple results with different match types."""
        # Arrange
        match_repo = Mock()
        token_repo = Mock()
        use_case = QueryResultsUseCase(
            match_repository=match_repo,
            lyric_token_repository=token_repo,
        )

        run_id = "run_mixed"
        corpus_id = "corpus_1"
        timestamp = datetime(2025, 12, 21, 12, 0, 0)
        input_text = "こんにちは トキョ"

        # Mock match results with mixed types
        match_result1 = MatchResult(
            input_token="こんにちは",
            input_reading="コンニチハ",
            match_type=MatchType.EXACT_SURFACE,
            matched_token_ids=["token_1"],
            mora_details=None,
        )

        mora_detail1 = MoraMatchDetail(mora="ト", source_token_id="token_2", mora_index=0)
        mora_detail2 = MoraMatchDetail(mora="キョ", source_token_id="token_3", mora_index=1)

        match_result2 = MatchResult(
            input_token="トキョ",
            input_reading="トキョ",
            match_type=MatchType.MORA_COMBINATION,
            matched_token_ids=[],
            mora_details=[mora_detail1, mora_detail2],
        )

        match_run = MatchRun(
            run_id=run_id,
            lyrics_corpus_id=corpus_id,
            input_text=input_text,
            timestamp=timestamp,
            config={},
            results=[match_result1, match_result2],
        )

        match_repo.find_by_id.return_value = match_run

        # Mock tokens
        token1 = LyricToken(
            token_id="token_1",
            lyrics_corpus_id=corpus_id,
            line_index=0,
            token_index=0,
            surface="こんにちは",
            reading=Reading(raw="コンニチハ"),
            lemma="こんにちは",
            pos="感動詞",
        )
        token2 = LyricToken(
            token_id="token_2",
            lyrics_corpus_id=corpus_id,
            line_index=0,
            token_index=1,
            surface="東",
            reading=Reading(raw="トウ"),
            lemma="東",
            pos="名詞",
        )
        token3 = LyricToken(
            token_id="token_3",
            lyrics_corpus_id=corpus_id,
            line_index=0,
            token_index=2,
            surface="京都",
            reading=Reading(raw="キョウト"),
            lemma="京都",
            pos="名詞",
        )

        token_repo.get_by_id.side_effect = lambda tid: (
            {"token_1": token1, "token_2": token2, "token_3": token3}.get(tid)
        )

        # Act
        result = use_case.execute(run_id)

        # Assert
        assert result is not None
        assert isinstance(result, QueryResultsDto)
        assert len(result.items) == 2
        assert result.items[0].match_type == MatchType.EXACT_SURFACE
        assert result.items[1].match_type == MatchType.MORA_COMBINATION
        assert result.summary.stats.exact_surface_count == 1
        assert result.summary.stats.mora_combination_count == 1
        # Verify reconstructed reading combines both
        assert "コンニチハ" in result.summary.reconstructed_reading
        assert "トキョ" in result.summary.reconstructed_reading
