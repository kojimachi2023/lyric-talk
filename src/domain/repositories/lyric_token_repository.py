"""
Repository interfaces (Ports)
DDD Onion Architecture におけるリポジトリの抽象インターフェース定義
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.lyric_token import LyricToken


class LyricTokenRepository(ABC):
    """
    歌詞トークンリポジトリのインターフェース

    歌詞トークンの永続化・検索を抽象化したインターフェース。
    実装はInfrastructure層で行う。
    """

    @abstractmethod
    def save(self, token: LyricToken) -> None:
        """
        歌詞トークンを保存する

        Args:
            token: 保存する歌詞トークン
        """
        pass

    @abstractmethod
    def save_many(self, tokens: List[LyricToken]) -> None:
        """
        複数の歌詞トークンを保存する

        Args:
            tokens: 保存する歌詞トークンのリスト
        """
        pass

    def save_batch(self, tokens: List[LyricToken]) -> None:
        """
        複数の歌詞トークンをバッチ保存する（エイリアス）

        save_many() のエイリアスメソッド。
        UseCaseから呼ばれる一般的な命名規則に合わせている。

        Args:
            tokens: 保存する歌詞トークンのリスト
        """
        return self.save_many(tokens)

    @abstractmethod
    def find_by_surface(self, surface: str, lyrics_corpus_id: str) -> List[LyricToken]:
        """
        表層形で歌詞トークンを検索する

        Args:
            surface: 検索する表層形
            lyrics_corpus_id: 検索対象の歌詞コーパスID

        Returns:
            マッチした歌詞トークンのリスト
        """
        pass

    @abstractmethod
    def find_by_reading(self, reading: str, lyrics_corpus_id: str) -> List[LyricToken]:
        """
        読みで歌詞トークンを検索する

        Args:
            reading: 検索する読み（カタカナ）
            lyrics_corpus_id: 検索対象の歌詞コーパスID

        Returns:
            マッチした歌詞トークンのリスト
        """
        pass

    @abstractmethod
    def find_by_mora(self, mora: str, lyrics_corpus_id: str) -> List[LyricToken]:
        """
        モーラで歌詞トークンを検索する

        Args:
            mora: 検索するモーラ
            lyrics_corpus_id: 検索対象の歌詞コーパスID

        Returns:
            指定されたモーラを含む歌詞トークンのリスト
        """
        pass

    @abstractmethod
    def find_by_token_id(self, token_id: str) -> Optional[LyricToken]:
        """
        トークンIDで歌詞トークンを取得する

        Args:
            token_id: トークンID

        Returns:
            マッチした歌詞トークン、見つからない場合はNone
        """
        pass

    def get_by_id(self, token_id: str) -> Optional[LyricToken]:
        """
        トークンIDで歌詞トークンを取得する（エイリアス）

        find_by_token_id() のエイリアスメソッド。
        UseCaseから呼ばれる一般的な命名規則に合わせている。

        Args:
            token_id: トークンID

        Returns:
            マッチした歌詞トークン、見つからない場合はNone
        """
        return self.find_by_token_id(token_id)

    @abstractmethod
    def find_by_token_ids(self, token_ids: List[str]) -> List[LyricToken]:
        """
        複数のトークンIDで歌詞トークンを取得する

        Args:
            token_ids: トークンIDのリスト

        Returns:
            マッチした歌詞トークンのリスト
        """
        pass

    @abstractmethod
    def delete_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> None:
        """
        指定された歌詞コーパスIDに属するすべての歌詞トークンを削除する

        Args:
            lyrics_corpus_id: 削除する歌詞コーパスID
        """
        pass
