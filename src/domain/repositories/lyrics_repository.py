"""
Repository interfaces (Ports)
歌詞コーパスリポジトリのインターフェース定義
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.models.lyrics_corpus import LyricsCorpus


class LyricsRepository(ABC):
    """
    歌詞コーパスリポジトリのインターフェース

    歌詞コーパスのメタデータの永続化・検索を抽象化したインターフェース。
    実装はInfrastructure層で行う。
    """

    @abstractmethod
    def save(self, lyrics_corpus: LyricsCorpus) -> str:
        """
        歌詞コーパスを保存する

        Args:
            lyrics_corpus: 保存する歌詞コーパス

        Returns:
            保存した歌詞コーパスのID
        """
        pass

    @abstractmethod
    def find_by_id(self, lyrics_corpus_id: str) -> Optional[LyricsCorpus]:
        """
        IDで歌詞コーパスを検索する

        Args:
            lyrics_corpus_id: 検索する歌詞コーパスID

        Returns:
            マッチした歌詞コーパス、見つからない場合はNone
        """
        pass

    @abstractmethod
    def find_by_content_hash(self, content_hash: str) -> Optional[LyricsCorpus]:
        """
        コンテンツハッシュで歌詞コーパスを検索する

        重複チェックに使用する（RegisterLyricsUseCaseで内部的に使用）。
        同一の歌詞テキストが既に登録されているかを判定する。

        Args:
            content_hash: 検索するコンテンツハッシュ（SHA256等）

        Returns:
            マッチした歌詞コーパス、見つからない場合はNone
        """
        pass

    @abstractmethod
    def find_by_title(self, title: str) -> list[LyricsCorpus]:
        """
        タイトルで歌詞コーパスを検索する

        ユーザーがタイトルから歌詞を検索する際に使用する。
        部分一致検索を行う（LIKE検索）。

        Args:
            title: 検索するタイトル（部分一致）

        Returns:
            マッチした歌詞コーパスのリスト（空の場合は空リスト）
        """
        pass

    @abstractmethod
    def delete(self, lyrics_corpus_id: str) -> None:
        """
        歌詞コーパスを削除する

        Args:
            lyrics_corpus_id: 削除する歌詞コーパスID
        """
        pass

    @abstractmethod
    def list_lyrics_corpora(self, limit: int) -> list[LyricsCorpus]:
        """
        最近追加された歌詞コーパスのリストを取得する

        CLI対話選択機能で使用。作成日時の降順で返す。

        Args:
            limit: 取得する最大件数

        Returns:
            歌詞コーパスのリスト（新しい順）
        """
        pass
