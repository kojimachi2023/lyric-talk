"""
MatchingStrategy domain service
マッチング戦略を実装するドメインサービス
"""

from typing import List, Optional

from src.domain.models.match_result import (
    MatchResult,
    MatchType,
    MoraMatchDetail,
)
from src.domain.models.mora import Mora
from src.domain.repositories.lyric_token_repository import LyricTokenRepository


class MatchingStrategy:
    """
    マッチング戦略ドメインサービス

    入力トークンを歌詞トークンとマッチングするための3段階戦略を実装：
    1. 表層形完全一致（EXACT_SURFACE）
    2. 読み完全一致（EXACT_READING）
    3. モーラ組み合わせ（MORA_COMBINATION）

    Attributes:
        repository: 歌詞トークンリポジトリ
        lyrics_corpus_id: 検索対象の歌詞コーパスID
        max_mora_length: モーラマッチングの最大長
    """

    def __init__(
        self,
        repository: LyricTokenRepository,
        lyrics_corpus_id: str,
        max_mora_length: int = 10,
    ):
        """
        Args:
            repository: 歌詞トークンリポジトリ
            lyrics_corpus_id: 検索対象の歌詞コーパスID
            max_mora_length: モーラマッチングの最大長（デフォルト: 10）
        """
        self.repository = repository
        self.lyrics_corpus_id = lyrics_corpus_id
        self.max_mora_length = max_mora_length

    def match_token(self, surface: str, reading: str, pos: str) -> MatchResult:
        """
        単一トークンをマッチングする

        3段階の優先度でマッチングを試行：
        1. 表層形完全一致
        2. 読み完全一致
        3. モーラ組み合わせ

        Args:
            surface: 入力トークンの表層形
            reading: 入力トークンの読み（カタカナ）
            pos: 入力トークンの品詞

        Returns:
            マッチング結果
        """
        # 1. 表層形完全一致
        tokens = self.repository.find_by_surface(surface, self.lyrics_corpus_id)
        if tokens:
            return MatchResult(
                input_token=surface,
                input_reading=reading,
                match_type=MatchType.EXACT_SURFACE,
                matched_token_ids=[tokens[0].token_id],
                mora_details=None,
            )

        # 2. 読み完全一致
        tokens = self.repository.find_by_reading(reading, self.lyrics_corpus_id)
        if tokens:
            return MatchResult(
                input_token=surface,
                input_reading=reading,
                match_type=MatchType.EXACT_READING,
                matched_token_ids=[tokens[0].token_id],
                mora_details=None,
            )

        # 3. モーラ組み合わせ
        mora_details = self._find_mora_combination(reading)
        if mora_details:
            return MatchResult(
                input_token=surface,
                input_reading=reading,
                match_type=MatchType.MORA_COMBINATION,
                matched_token_ids=[],
                mora_details=mora_details,
            )

        # マッチなし
        return MatchResult(
            input_token=surface,
            input_reading=reading,
            match_type=MatchType.NO_MATCH,
            matched_token_ids=[],
            mora_details=None,
        )

    def _find_mora_combination(self, reading: str) -> Optional[List[MoraMatchDetail]]:
        """
        モーラ組み合わせでマッチングする（前方マッチング）

        個々のモーラ単位で歌詞中のトークンから前方順にマッチングを行う。
        各モーラは独立して歌詞トークンから取得できる。

        Args:
            reading: 読み（カタカナ）

        Returns:
            マッチした場合はMoraMatchDetailのリスト、なければNone
        """
        target_moras = Mora.split(reading)
        n = len(target_moras)

        if n == 0:
            return None

        # モーラ数が設定値を超える場合はスキップ
        if n > self.max_mora_length:
            return None

        result: List[MoraMatchDetail] = []

        # 各モーラを前から順にマッチング
        for mora in target_moras:
            tokens = self.repository.find_by_mora(mora.value, self.lyrics_corpus_id)
            if not tokens:
                # 入力モーラのマッチングに一つでも失敗したら終了
                return None

            # 最初に見つかったトークンを使用
            token = tokens[0]
            # トークン内でのモーラ位置を取得
            mora_index = token.moras.index(mora) if mora in token.moras else 0
            result.append(
                MoraMatchDetail(
                    mora=mora.value,
                    source_token_id=token.token_id,
                    mora_index=mora_index,
                )
            )

        return result
