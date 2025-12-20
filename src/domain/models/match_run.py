"""
MatchRun entity (Aggregate Root)
マッチング実行を表すエンティティ（集約ルート）
"""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field

# Avoid circular import by importing at runtime
# Note: MatchResult import is done lazily for forward reference resolution


class MatchRun(BaseModel):
    """
    マッチング実行エンティティ（集約ルート）

    1回のマッチング実行セッションを表すエンティティです。
    入力テキスト、使用した設定、タイムスタンプ、マッチング結果を管理します。

    DDDの集約として、MatchResultを子エンティティとして持ちます。
    エンティティなので可変（mutable）です。

    Attributes:
        run_id: マッチング実行の一意識別子（UUID推奨）
        lyrics_corpus_id: 使用した歌詞コーパスのID
        timestamp: 実行日時
        input_text: 入力テキスト
        config: マッチング設定（max_mora_length等）
        results: マッチング結果のリスト（子エンティティ）
    """

    run_id: str
    lyrics_corpus_id: str
    timestamp: datetime
    input_text: str
    config: Dict[str, Any]
    results: List[Any] = Field(
        default_factory=list
    )  # List[MatchResult], using Any to avoid circular import

    # エンティティは可変なのでfrozen=Falseがデフォルト（明示的に設定）
    model_config = {"frozen": False}

    def add_result(self, result: Any) -> None:
        """マッチング結果を追加する。

        Args:
            result: 追加するマッチング結果 (MatchResult)
        """
        self.results.append(result)
