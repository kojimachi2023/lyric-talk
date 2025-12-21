"""
Repository interfaces (Ports)
マッチング結果リポジトリのインターフェース定義
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.match_run import MatchRun


class MatchRepository(ABC):
    """
    マッチング結果リポジトリのインターフェース

    MatchRun集約（MatchRun + MatchResultの集合）の永続化・検索を抽象化したインターフェース。
    実装はInfrastructure層で行う。

    Note:
        DDDの集約パターンに従い、MatchRunを集約ルートとして扱う。
        MatchResultはMatchRunの子エンティティとして、集約ルート経由で保存・取得される。
    """

    @abstractmethod
    def save(self, match_run: MatchRun) -> str:
        """
        マッチング実行（集約全体）を保存する

        MatchRunとその子エンティティであるMatchResult（results）を
        トランザクション内で一括保存する。

        Args:
            match_run: 保存するマッチング実行情報（results含む）

        Returns:
            保存したマッチング実行ID
        """
        pass

    @abstractmethod
    def find_by_id(self, run_id: str) -> Optional[MatchRun]:
        """
        IDでマッチング実行情報を検索する

        MatchRunとその子エンティティであるMatchResultを含めて取得する。

        Args:
            run_id: 検索するマッチング実行ID

        Returns:
            マッチした実行情報（results含む）、見つからない場合はNone
        """
        pass

    @abstractmethod
    def find_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> List[MatchRun]:
        """
        歌詞コーパスIDでマッチング実行を検索する

        Args:
            lyrics_corpus_id: 検索する歌詞コーパスID

        Returns:
            マッチした実行情報のリスト（各MatchRunはresults含む）
        """
        pass

    @abstractmethod
    def delete(self, run_id: str) -> None:
        """
        マッチング実行とその結果を削除する

        Args:
            run_id: 削除するマッチング実行ID
        """
        pass

    @abstractmethod
    def list_match_runs(self, limit: int) -> list[MatchRun]:
        """
        最近実行されたマッチング実行のリストを取得する

        CLI対話選択機能で使用。タイムスタンプの降順で返す。

        Args:
            limit: 取得する最大件数

        Returns:
            マッチング実行のリスト（新しい順、results含む）
        """
        pass

    # エイリアスメソッド（後方互換性のため）
    def save_run(self, match_run: MatchRun) -> str:
        """save()のエイリアス（後方互換性）"""
        return self.save(match_run)

    def find_run_by_id(self, run_id: str) -> Optional[MatchRun]:
        """find_by_id()のエイリアス（後方互換性）"""
        return self.find_by_id(run_id)

    def find_runs_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> List[MatchRun]:
        """find_by_lyrics_corpus_id()のエイリアス（後方互換性）"""
        return self.find_by_lyrics_corpus_id(lyrics_corpus_id)

    def delete_run(self, run_id: str) -> None:
        """delete()のエイリアス（後方互換性）"""
        return self.delete(run_id)
