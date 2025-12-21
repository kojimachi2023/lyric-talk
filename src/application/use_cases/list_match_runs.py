"""
Application Use Case: List Match Runs
マッチング実行履歴一覧取得ユースケース
"""

from src.application.dtos.cli_summaries import MatchRunSummaryDto
from src.domain.repositories.match_repository import MatchRepository


class ListMatchRunsUseCase:
    """
    マッチング実行履歴一覧取得ユースケース

    保存されているマッチング実行履歴の一覧をサマリー情報として取得する。
    CLI の対話選択機能で使用するための概要情報を提供。
    """

    def __init__(self, match_repository: MatchRepository):
        """
        コンストラクタ

        Args:
            match_repository: マッチングリポジトリ
        """
        self._match_repository = match_repository

    def execute(self, limit: int = 10) -> list[MatchRunSummaryDto]:
        """
        マッチング実行履歴一覧を取得する

        Args:
            limit: 取得する最大件数（デフォルト: 10）

        Returns:
            マッチング実行サマリーDTOのリスト（新しい順）
        """
        # 最新のマッチング実行履歴を取得
        runs = self._match_repository.list_match_runs(limit)

        # 各実行のサマリー情報を構築
        summaries: list[MatchRunSummaryDto] = []
        for run in runs:
            # DTOを作成
            summary = MatchRunSummaryDto(
                run_id=run.run_id,
                lyrics_corpus_id=run.lyrics_corpus_id,
                timestamp=run.timestamp,
                input_text=run.input_text,
                results_count=len(run.results),
            )
            summaries.append(summary)

        return summaries
