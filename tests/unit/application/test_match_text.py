"""Tests for MatchTextUseCase (Red phase - TDD)."""

from unittest.mock import Mock

from src.application.dtos.token_data import TokenData
from src.application.use_cases.match_text import MatchTextUseCase


class TestMatchTextUseCase:
    """Test MatchTextUseCase."""

    def test_match_text_success(self):
        """Test matching text with successful matches."""
        # Arrange
        nlp_service = Mock()
        lyric_token_repo = Mock()
        match_repo = Mock()

        use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            lyric_token_repository=lyric_token_repo,
            match_repository=match_repo,
            max_mora_length=5,
        )

        input_text = "テストする"
        corpus_id = "corpus_123"

        # Mock: tokenization
        nlp_service.tokenize.return_value = [
            TokenData(surface="テスト", reading="テスト", lemma="テスト", pos="名詞"),
            TokenData(surface="する", reading="スル", lemma="する", pos="動詞"),
        ]

        # Mock: repository methods for matching strategy
        lyric_token_repo.find_by_surface.return_value = []
        lyric_token_repo.find_by_reading.return_value = []
        lyric_token_repo.find_by_mora.return_value = []  # No mora matches
        lyric_token_repo.find_all_by_corpus.return_value = []

        # Mock: save returns run_id
        match_repo.save.return_value = "run_123"

        # Act
        run_id = use_case.execute(input_text, corpus_id)

        # Assert
        assert run_id == "run_123"

        # Verify tokenization
        nlp_service.tokenize.assert_called_once_with(input_text)

        # Verify save called with aggregate (MatchRun with results)
        match_repo.save.assert_called_once()
        saved_run = match_repo.save.call_args[0][0]
        assert saved_run.lyrics_corpus_id == corpus_id

    def test_match_text_no_matches(self):
        """Test matching text with no matches."""
        # Arrange
        nlp_service = Mock()
        lyric_token_repo = Mock()
        match_repo = Mock()

        use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            lyric_token_repository=lyric_token_repo,
            match_repository=match_repo,
            max_mora_length=5,
        )

        input_text = "未登録"
        corpus_id = "corpus_456"

        # Mock: tokenization
        nlp_service.tokenize.return_value = [
            TokenData(surface="未登録", reading="ミトウロク", lemma="未登録", pos="名詞"),
        ]

        # Mock: repository methods - no matches
        lyric_token_repo.find_by_surface.return_value = []
        lyric_token_repo.find_by_reading.return_value = []
        lyric_token_repo.find_by_mora.return_value = []  # No mora matches

        # Mock: save returns run_id
        match_repo.save.return_value = "run_456"

        # Act
        run_id = use_case.execute(input_text, corpus_id)

        # Assert
        assert run_id == "run_456"

        # Verify save called with aggregate (NO_MATCH results are still added)
        match_repo.save.assert_called_once()
        saved_run = match_repo.save.call_args[0][0]
        assert len(saved_run.results) == 1
        assert saved_run.results[0].match_type.value == "no_match"

    def test_match_text_empty_input(self):
        """Test matching empty text (edge case)."""
        # Arrange
        nlp_service = Mock()
        lyric_token_repo = Mock()
        match_repo = Mock()

        use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            lyric_token_repository=lyric_token_repo,
            match_repository=match_repo,
            max_mora_length=5,
        )

        input_text = ""
        corpus_id = "corpus_empty"

        # Mock: tokenization returns empty
        nlp_service.tokenize.return_value = []

        # Mock: save returns run_id
        match_repo.save.return_value = "run_empty"

        # Act
        run_id = use_case.execute(input_text, corpus_id)

        # Assert
        assert run_id == "run_empty"

        # Verify save called with aggregate (MatchRun with empty results)
        match_repo.save.assert_called_once()
        saved_run = match_repo.save.call_args[0][0]
        assert len(saved_run.results) == 0
