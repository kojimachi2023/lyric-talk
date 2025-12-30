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
        uow = Mock()
        uow.lyric_token_repository = Mock()
        uow.match_repository = Mock()

        use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            unit_of_work=uow,
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
        uow.lyric_token_repository.find_by_surface.return_value = []
        uow.lyric_token_repository.find_by_reading.return_value = []
        uow.lyric_token_repository.find_by_mora.return_value = []  # No mora matches
        uow.lyric_token_repository.find_all_by_corpus.return_value = []

        # Mock: save returns run_id
        uow.match_repository.save.return_value = "run_123"

        # Act
        run_id = use_case.execute(input_text, corpus_id)

        # Assert
        assert run_id == "run_123"

        # Verify tokenization
        nlp_service.tokenize.assert_called_once_with(input_text)

        # Verify save called with aggregate (MatchRun with results)
        uow.match_repository.save.assert_called_once()
        saved_run = uow.match_repository.save.call_args[0][0]
        assert saved_run.lyrics_corpus_id == corpus_id

    def test_match_text_no_matches(self):
        """Test matching text with no matches."""
        # Arrange
        nlp_service = Mock()
        uow = Mock()
        uow.lyric_token_repository = Mock()
        uow.match_repository = Mock()

        use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            unit_of_work=uow,
            max_mora_length=5,
        )

        input_text = "未登録"
        corpus_id = "corpus_456"

        # Mock: tokenization
        nlp_service.tokenize.return_value = [
            TokenData(surface="未登録", reading="ミトウロク", lemma="未登録", pos="名詞"),
        ]

        # Mock: repository methods - no matches
        uow.lyric_token_repository.find_by_surface.return_value = []
        uow.lyric_token_repository.find_by_reading.return_value = []
        uow.lyric_token_repository.find_by_mora.return_value = []  # No mora matches

        # Mock: save returns run_id
        uow.match_repository.save.return_value = "run_456"

        # Act
        run_id = use_case.execute(input_text, corpus_id)

        # Assert
        assert run_id == "run_456"

        # Verify save called with aggregate (NO_MATCH results are still added)
        uow.match_repository.save.assert_called_once()
        saved_run = uow.match_repository.save.call_args[0][0]
        assert len(saved_run.results) == 1
        assert saved_run.results[0].match_type.value == "no_match"

    def test_match_text_empty_input(self):
        """Test matching empty text (edge case)."""
        # Arrange
        nlp_service = Mock()
        uow = Mock()
        uow.lyric_token_repository = Mock()
        uow.match_repository = Mock()

        use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            unit_of_work=uow,
            max_mora_length=5,
        )

        input_text = ""
        corpus_id = "corpus_empty"

        # Mock: tokenization returns empty
        nlp_service.tokenize.return_value = []

        # Mock: save returns run_id
        uow.match_repository.save.return_value = "run_empty"

        # Act
        run_id = use_case.execute(input_text, corpus_id)

        # Assert
        assert run_id == "run_empty"

        # Verify save called with aggregate (MatchRun with empty results)
        uow.match_repository.save.assert_called_once()
        saved_run = uow.match_repository.save.call_args[0][0]
        assert len(saved_run.results) == 0
