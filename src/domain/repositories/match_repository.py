"""
Repository interfaces (Ports)
マッチング結果リポジトリのインターフェース定義
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.match_result import MatchResult
from src.domain.models.match_run import MatchRun


class MatchRepository(ABC):
    """
    マッチング結果リポジトリのインターフェース

    マッチング実行とその結果の永続化・検索を抽象化したインターフェース。
    実装はInfrastructure層で行う。
    """

    @abstractmethod
    def save_run(self, match_run: MatchRun) -> None:
        """
        マッチング実行情報を保存する

        Args:
            match_run: 保存するマッチング実行情報
        """
        pass

    @abstractmethod
    def save_results(self, run_id: str, results: List[MatchResult]) -> None:
        """
        マッチング結果を保存する

        Args:
            run_id: マッチング実行ID
            results: 保存するマッチング結果のリスト
        """
        pass

    @abstractmethod
    def find_run_by_id(self, run_id: str) -> Optional[MatchRun]:
        """
        IDでマッチング実行情報を検索する

        Args:
            run_id: 検索するマッチング実行ID

        Returns:
            マッチした実行情報、見つからない場合はNone
        """
        pass

    @abstractmethod
    def find_results_by_run_id(self, run_id: str) -> List[MatchResult]:
        """
        実行IDでマッチング結果を検索する

        Args:
            run_id: 検索するマッチング実行ID

        Returns:
            マッチした結果のリスト
        """
        pass

    @abstractmethod
    def find_runs_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> List[MatchRun]:
        """
        歌詞コーパスIDでマッチング実行を検索する

        Args:
            lyrics_corpus_id: 検索する歌詞コーパスID

        Returns:
            マッチした実行情報のリスト
        """
        pass

    @abstractmethod
    def delete_run(self, run_id: str) -> None:
        """
        マッチング実行とその結果を削除する

        Args:
            run_id: 削除するマッチング実行ID
        """
        pass
