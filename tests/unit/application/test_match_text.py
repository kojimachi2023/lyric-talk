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
        matching_strategy = Mock()
        match_repo = Mock()

        use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            matching_strategy=matching_strategy,
            match_repository=match_repo,
        )

        input_text = "テストする"

        # Mock: tokenization
        nlp_service.tokenize.return_value = [
            TokenData(surface="テスト", reading="テスト", lemma="テスト", pos="名詞"),
            TokenData(surface="する", reading="スル", lemma="する", pos="動詞"),
        ]

        # Mock: matching results
        match_result1 = Mock()
        match_result1.matched_token_ids = ["token_1"]

        match_result2 = Mock()
        match_result2.matched_token_ids = ["token_2"]

        matching_strategy.match_token.side_effect = [match_result1, match_result2]

        # Mock: save returns run_id
        match_repo.save.return_value = "run_123"

        # Act
        run_id = use_case.execute(input_text)

        # Assert
        assert run_id == "run_123"

        # Verify tokenization
        nlp_service.tokenize.assert_called_once_with(input_text)

        # Verify matching
        assert matching_strategy.match_token.call_count == 2

        # Verify save called with aggregate (MatchRun with results)
        match_repo.save.assert_called_once()
        saved_run = match_repo.save.call_args[0][0]
        assert len(saved_run.results) == 2

    def test_match_text_no_matches(self):
        """Test matching text with no matches."""
        # Arrange
        nlp_service = Mock()
        matching_strategy = Mock()
        match_repo = Mock()

        use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            matching_strategy=matching_strategy,
            match_repository=match_repo,
        )

        input_text = "未登録"

        # Mock: tokenization
        nlp_service.tokenize.return_value = [
            TokenData(surface="未登録", reading="ミトウロク", lemma="未登録", pos="名詞"),
        ]

        # Mock: no matches
        matching_strategy.match_token.return_value = None

        # Mock: save returns run_id
        match_repo.save.return_value = "run_456"

        # Act
        run_id = use_case.execute(input_text)

        # Assert
        assert run_id == "run_456"

        # Verify save called with aggregate (MatchRun with empty results)
        match_repo.save.assert_called_once()
        saved_run = match_repo.save.call_args[0][0]
        assert len(saved_run.results) == 0

    def test_match_text_empty_input(self):
        """Test matching empty text (edge case)."""
        # Arrange
        nlp_service = Mock()
        matching_strategy = Mock()
        match_repo = Mock()

        use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            matching_strategy=matching_strategy,
            match_repository=match_repo,
        )

        input_text = ""

        # Mock: tokenization returns empty
        nlp_service.tokenize.return_value = []

        # Mock: save returns run_id
        match_repo.save.return_value = "run_empty"

        # Act
        run_id = use_case.execute(input_text)

        # Assert
        assert run_id == "run_empty"

        # Verify matching not called
        matching_strategy.match_token.assert_not_called()

        # Verify save called with aggregate (MatchRun with empty results)
        match_repo.save.assert_called_once()
        saved_run = match_repo.save.call_args[0][0]
        assert len(saved_run.results) == 0
