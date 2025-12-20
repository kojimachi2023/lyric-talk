"""
Test MatchingStrategy domain service (TDD Red phase)
MatchingStrategyドメインサービスのテスト
"""

from unittest.mock import Mock

import pytest

from src.domain.models.lyric_token import LyricToken
from src.domain.models.match_result import MatchType
from src.domain.models.reading import Reading
from src.domain.repositories.lyric_token_repository import LyricTokenRepository
from src.domain.services.matching_strategy import MatchingStrategy


# このテストは実装前に失敗するべき（Red phase）
class TestMatchingStrategy:
    """MatchingStrategyドメインサービスのテスト"""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """モックされたLyricTokenRepositoryを返す"""
        return Mock(spec=LyricTokenRepository)

    @pytest.fixture
    def sample_tokens(self) -> list[LyricToken]:
        """テスト用の歌詞トークンサンプル"""
        return [
            LyricToken(
                lyrics_corpus_id="corpus_1",
                surface="東京",
                reading=Reading(raw="トウキョウ"),
                lemma="東京",
                pos="NOUN",
                line_index=0,
                token_index=0,
            ),
            LyricToken(
                lyrics_corpus_id="corpus_1",
                surface="学校",
                reading=Reading(raw="ガッコウ"),
                lemma="学校",
                pos="NOUN",
                line_index=0,
                token_index=1,
            ),
            LyricToken(
                lyrics_corpus_id="corpus_1",
                surface="歌う",
                reading=Reading(raw="ウタウ"),
                lemma="歌う",
                pos="VERB",
                line_index=1,
                token_index=0,
            ),
        ]

    def test_exact_surface_match(
        self, mock_repository: Mock, sample_tokens: list[LyricToken]
    ) -> None:
        """表層形完全一致のテスト"""
        # モックの設定：「東京」を検索すると最初のトークンが返る
        mock_repository.find_by_surface.return_value = [sample_tokens[0]]
        mock_repository.find_by_reading.return_value = []

        strategy = MatchingStrategy(mock_repository, lyrics_corpus_id="corpus_1")
        result = strategy.match_token(surface="東京", reading="トウキョウ", pos="NOUN")

        # 検証
        assert result.match_type == MatchType.EXACT_SURFACE
        assert result.input_token == "東京"
        assert result.input_reading == "トウキョウ"
        assert len(result.matched_token_ids) == 1
        assert result.matched_token_ids[0] == "corpus_1_0_0"
        assert result.mora_details is None

        # リポジトリが正しく呼ばれたか確認
        mock_repository.find_by_surface.assert_called_once_with("東京", "corpus_1")

    def test_exact_reading_match(
        self, mock_repository: Mock, sample_tokens: list[LyricToken]
    ) -> None:
        """読み完全一致のテスト"""
        # モックの設定：表層形では見つからず、読みで見つかる
        mock_repository.find_by_surface.return_value = []
        mock_repository.find_by_reading.return_value = [sample_tokens[2]]

        strategy = MatchingStrategy(mock_repository, lyrics_corpus_id="corpus_1")
        result = strategy.match_token(surface="唄う", reading="ウタウ", pos="VERB")

        # 検証
        assert result.match_type == MatchType.EXACT_READING
        assert result.input_token == "唄う"
        assert result.input_reading == "ウタウ"
        assert len(result.matched_token_ids) == 1
        assert result.matched_token_ids[0] == "corpus_1_1_0"
        assert result.mora_details is None

        # リポジトリの呼び出し確認
        mock_repository.find_by_surface.assert_called_once_with("唄う", "corpus_1")
        mock_repository.find_by_reading.assert_called_once_with("ウタウ", "corpus_1")

    def test_mora_combination_match(
        self, mock_repository: Mock, sample_tokens: list[LyricToken]
    ) -> None:
        """モーラ組み合わせマッチのテスト"""
        # モックの設定：表層形・読みでは見つからない
        mock_repository.find_by_surface.return_value = []
        mock_repository.find_by_reading.return_value = []

        # モーラ検索のモック：「ト」→東京、「キョ」→東京
        def mock_find_by_mora(mora: str, corpus_id: str):
            if mora == "ト":
                return [sample_tokens[0]]  # 東京（トウキョウ）
            elif mora == "キョ":
                return [sample_tokens[0]]  # 東京（トウキョウ）
            return []

        mock_repository.find_by_mora.side_effect = mock_find_by_mora

        strategy = MatchingStrategy(mock_repository, lyrics_corpus_id="corpus_1", max_mora_length=4)
        result = strategy.match_token(surface="トキョ", reading="トキョ", pos="NOUN")

        # 検証
        assert result.match_type == MatchType.MORA_COMBINATION
        assert result.input_token == "トキョ"
        assert result.input_reading == "トキョ"
        assert result.mora_details is not None
        assert len(result.mora_details) == 2
        # 最初のモーラ「ト」
        assert result.mora_details[0].mora == "ト"
        assert result.mora_details[0].source_token_id == "corpus_1_0_0"
        # 2番目のモーラ「キョ」
        assert result.mora_details[1].mora == "キョ"
        assert result.mora_details[1].source_token_id == "corpus_1_0_0"

    def test_no_match(self, mock_repository: Mock) -> None:
        """マッチなしのテスト"""
        # すべて空リストを返す
        mock_repository.find_by_surface.return_value = []
        mock_repository.find_by_reading.return_value = []
        mock_repository.find_by_mora.return_value = []

        strategy = MatchingStrategy(mock_repository, lyrics_corpus_id="corpus_1")
        result = strategy.match_token(surface="存在しない", reading="ソンザイシナイ", pos="VERB")

        # 検証
        assert result.match_type == MatchType.NO_MATCH
        assert result.input_token == "存在しない"
        assert result.input_reading == "ソンザイシナイ"
        assert len(result.matched_token_ids) == 0
        assert result.mora_details is None

    def test_mora_match_respects_max_length(
        self, mock_repository: Mock, sample_tokens: list[LyricToken]
    ) -> None:
        """max_mora_lengthを超える場合はモーラマッチしないテスト"""
        mock_repository.find_by_surface.return_value = []
        mock_repository.find_by_reading.return_value = []

        # max_mora_length=2に設定
        strategy = MatchingStrategy(mock_repository, lyrics_corpus_id="corpus_1", max_mora_length=2)

        # 3モーラの読みを渡す
        result = strategy.match_token(surface="トウキョウ", reading="トウキョウ", pos="NOUN")

        # max_mora_lengthを超えるため、モーラマッチは試行されずNO_MATCH
        assert result.match_type == MatchType.NO_MATCH

        # find_by_moraは呼ばれないはず
        mock_repository.find_by_mora.assert_not_called()
