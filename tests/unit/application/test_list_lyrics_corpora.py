"""Tests for ListLyricsCorporaUseCase (TDD - Red phase)."""

from datetime import datetime
from unittest.mock import Mock

from src.application.dtos.cli_summaries import LyricsCorpusSummaryDto
from src.application.use_cases.list_lyrics_corpora import ListLyricsCorporaUseCase
from src.domain.models.lyric_token import LyricToken
from src.domain.models.lyrics_corpus import LyricsCorpus
from src.domain.models.reading import Reading


class TestListLyricsCorporaUseCase:
    """Test ListLyricsCorporaUseCase."""

    def test_list_empty_corpora(self):
        """Test listing when no corpora exist."""
        # Arrange
        uow = Mock()
        uow.lyrics_repository = Mock()
        uow.lyric_token_repository = Mock()

        use_case = ListLyricsCorporaUseCase(unit_of_work=uow)

        # Mock: no corpora exist
        uow.lyrics_repository.list_lyrics_corpora.return_value = []

        # Act
        result = use_case.execute(limit=10)

        # Assert
        assert result == []
        uow.lyrics_repository.list_lyrics_corpora.assert_called_once_with(10)
        uow.lyric_token_repository.count_by_lyrics_corpus_id.assert_not_called()
        uow.lyric_token_repository.list_by_lyrics_corpus_id.assert_not_called()

    def test_list_single_corpus(self):
        """Test listing with a single corpus."""
        # Arrange
        uow = Mock()
        uow.lyrics_repository = Mock()
        uow.lyric_token_repository = Mock()

        use_case = ListLyricsCorporaUseCase(unit_of_work=uow)

        # Mock data
        corpus = LyricsCorpus(
            lyrics_corpus_id="corpus_1",
            content_hash="hash_1",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            title="Test Song",
            artist="Test Artist",
        )
        uow.lyrics_repository.list_lyrics_corpora.return_value = [corpus]

        # Mock token data
        uow.lyric_token_repository.count_by_lyrics_corpus_id.return_value = 5
        uow.lyric_token_repository.list_by_lyrics_corpus_id.return_value = [
            LyricToken(
                lyrics_corpus_id="corpus_1",
                surface="テスト",
                reading=Reading(raw="テスト"),
                lemma="テスト",
                pos="名詞",
                line_index=0,
                token_index=0,
            ),
            LyricToken(
                lyrics_corpus_id="corpus_1",
                surface="の",
                reading=Reading(raw="ノ"),
                lemma="の",
                pos="助詞",
                line_index=0,
                token_index=1,
            ),
            LyricToken(
                lyrics_corpus_id="corpus_1",
                surface="歌詞",
                reading=Reading(raw="カシ"),
                lemma="歌詞",
                pos="名詞",
                line_index=0,
                token_index=2,
            ),
        ]

        # Act
        result = use_case.execute(limit=10, max_preview_token=5)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], LyricsCorpusSummaryDto)
        assert result[0].lyrics_corpus_id == "corpus_1"
        assert result[0].title == "Test Song"
        assert result[0].artist == "Test Artist"
        assert result[0].created_at == datetime(2025, 1, 1, 12, 0, 0)
        assert result[0].token_count == 5
        assert result[0].preview_text == "テストの歌詞"

        uow.lyrics_repository.list_lyrics_corpora.assert_called_once_with(10)
        uow.lyric_token_repository.count_by_lyrics_corpus_id.assert_called_once_with("corpus_1")
        uow.lyric_token_repository.list_by_lyrics_corpus_id.assert_called_once_with(
            "corpus_1", limit=5
        )

    def test_list_multiple_corpora(self):
        """Test listing with multiple corpora."""
        # Arrange
        uow = Mock()
        uow.lyrics_repository = Mock()
        uow.lyric_token_repository = Mock()

        use_case = ListLyricsCorporaUseCase(unit_of_work=uow)

        # Mock data
        corpus1 = LyricsCorpus(
            lyrics_corpus_id="corpus_1",
            content_hash="hash_1",
            created_at=datetime(2025, 1, 2, 12, 0, 0),
            title="Song A",
            artist="Artist A",
        )
        corpus2 = LyricsCorpus(
            lyrics_corpus_id="corpus_2",
            content_hash="hash_2",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            title=None,
            artist=None,
        )
        uow.lyrics_repository.list_lyrics_corpora.return_value = [corpus1, corpus2]

        # Mock token data for corpus1
        def count_side_effect(corpus_id):
            if corpus_id == "corpus_1":
                return 3
            elif corpus_id == "corpus_2":
                return 2
            return 0

        def list_side_effect(corpus_id, limit):
            if corpus_id == "corpus_1":
                return [
                    LyricToken(
                        lyrics_corpus_id="corpus_1",
                        surface="歌詞",
                        reading=Reading(raw="カシ"),
                        lemma="歌詞",
                        pos="名詞",
                        line_index=0,
                        token_index=0,
                    ),
                    LyricToken(
                        lyrics_corpus_id="corpus_1",
                        surface="A",
                        reading=Reading(raw="エー"),
                        lemma="A",
                        pos="名詞",
                        line_index=0,
                        token_index=1,
                    ),
                ]
            elif corpus_id == "corpus_2":
                return [
                    LyricToken(
                        lyrics_corpus_id="corpus_2",
                        surface="歌詞",
                        reading=Reading(raw="カシ"),
                        lemma="歌詞",
                        pos="名詞",
                        line_index=0,
                        token_index=0,
                    ),
                ]
            return []

        uow.lyric_token_repository.count_by_lyrics_corpus_id.side_effect = count_side_effect
        uow.lyric_token_repository.list_by_lyrics_corpus_id.side_effect = list_side_effect

        # Act
        result = use_case.execute(limit=10)

        # Assert
        assert len(result) == 2
        assert all(isinstance(dto, LyricsCorpusSummaryDto) for dto in result)

        # Check first corpus
        assert result[0].lyrics_corpus_id == "corpus_1"
        assert result[0].title == "Song A"
        assert result[0].artist == "Artist A"
        assert result[0].token_count == 3
        assert result[0].preview_text == "歌詞A"

        # Check second corpus
        assert result[1].lyrics_corpus_id == "corpus_2"
        assert result[1].title is None
        assert result[1].artist is None
        assert result[1].token_count == 2
        assert result[1].preview_text == "歌詞"

    def test_list_respects_limit(self):
        """Test that the limit parameter is passed to repository."""
        # Arrange
        uow = Mock()
        uow.lyrics_repository = Mock()
        uow.lyric_token_repository = Mock()

        use_case = ListLyricsCorporaUseCase(unit_of_work=uow)

        uow.lyrics_repository.list_lyrics_corpora.return_value = []

        # Act
        use_case.execute(limit=5)

        # Assert
        uow.lyrics_repository.list_lyrics_corpora.assert_called_once_with(5)
