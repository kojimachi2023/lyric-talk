"""Tests for RegisterLyricsUseCase (Red phase - TDD)."""

from unittest.mock import Mock

from src.application.dtos.token_data import TokenData
from src.application.use_cases.register_lyrics import RegisterLyricsUseCase
from src.domain.models.lyric_token import LyricToken
from src.domain.models.lyrics_corpus import LyricsCorpus


class TestRegisterLyricsUseCase:
    """Test RegisterLyricsUseCase."""

    def test_register_new_lyrics(self):
        """Test registering new lyrics (corpus doesn't exist)."""
        # Arrange
        nlp_service = Mock()
        lyrics_repo = Mock()
        token_repo = Mock()

        use_case = RegisterLyricsUseCase(
            nlp_service=nlp_service,
            lyrics_repository=lyrics_repo,
            lyric_token_repository=token_repo,
        )

        lyrics_text = "テスト\nサンプル"

        # Mock: corpus doesn't exist (new registration)
        lyrics_repo.find_by_content_hash.return_value = None
        lyrics_repo.save.return_value = "corpus_123"

        # Mock: tokenization
        nlp_service.tokenize.return_value = [
            TokenData(surface="テスト", reading="テスト", lemma="テスト", pos="名詞"),
            TokenData(surface="サンプル", reading="サンプル", lemma="サンプル", pos="名詞"),
        ]

        # Act
        corpus_id = use_case.execute(lyrics_text)

        # Assert
        assert corpus_id == "corpus_123"

        # Verify hash check
        lyrics_repo.find_by_content_hash.assert_called_once()

        # Verify tokenization
        nlp_service.tokenize.assert_called_once_with(lyrics_text)

        # Verify corpus saved
        lyrics_repo.save.assert_called_once()
        saved_corpus = lyrics_repo.save.call_args[0][0]
        assert isinstance(saved_corpus, LyricsCorpus)

        # Verify tokens saved
        token_repo.save_batch.assert_called_once()
        saved_tokens = token_repo.save_batch.call_args[0][0]
        assert len(saved_tokens) == 2
        assert all(isinstance(token, LyricToken) for token in saved_tokens)

    def test_register_duplicate_lyrics(self):
        """Test registering duplicate lyrics (reuse existing corpus_id)."""
        # Arrange
        nlp_service = Mock()
        lyrics_repo = Mock()
        token_repo = Mock()

        use_case = RegisterLyricsUseCase(
            nlp_service=nlp_service,
            lyrics_repository=lyrics_repo,
            lyric_token_repository=token_repo,
        )

        lyrics_text = "重複テスト"

        # Mock: corpus already exists
        from datetime import datetime

        existing_corpus = LyricsCorpus(
            lyrics_corpus_id="existing_corpus_456",
            content_hash="hash_abc",
            created_at=datetime.now(),
        )
        lyrics_repo.find_by_content_hash.return_value = existing_corpus

        # Act
        corpus_id = use_case.execute(lyrics_text)

        # Assert
        assert corpus_id == "existing_corpus_456"

        # Verify hash check
        lyrics_repo.find_by_content_hash.assert_called_once()

        # Verify NO tokenization or saving
        nlp_service.tokenize.assert_not_called()
        lyrics_repo.save.assert_not_called()
        token_repo.save_batch.assert_not_called()

    def test_register_empty_lyrics(self):
        """Test registering empty lyrics (edge case)."""
        # Arrange
        nlp_service = Mock()
        lyrics_repo = Mock()
        token_repo = Mock()

        use_case = RegisterLyricsUseCase(
            nlp_service=nlp_service,
            lyrics_repository=lyrics_repo,
            lyric_token_repository=token_repo,
        )

        lyrics_text = ""

        # Mock
        lyrics_repo.find_by_content_hash.return_value = None
        lyrics_repo.save.return_value = "corpus_empty"
        nlp_service.tokenize.return_value = []

        # Act
        corpus_id = use_case.execute(lyrics_text)

        # Assert
        assert corpus_id == "corpus_empty"
        token_repo.save_batch.assert_called_once_with([])
