"""
MatchRun entity
マッチング実行を表すエンティティ
"""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel


class MatchRun(BaseModel):
    """
    マッチング実行エンティティ

    1回のマッチング実行セッションを表すエンティティです。
    入力テキスト、使用した設定、タイムスタンプなどを記録します。
    エンティティなので可変（mutable）です。

    Attributes:
        run_id: マッチング実行の一意識別子（UUID推奨）
        lyrics_corpus_id: 使用した歌詞コーパスのID
        timestamp: 実行日時
        input_text: 入力テキスト
        config: マッチング設定（max_mora_length等）
    """

    run_id: str
    lyrics_corpus_id: str
    timestamp: datetime
    input_text: str
    config: Dict[str, Any]

    # エンティティは可変なのでfrozen=Falseがデフォルト（明示的に設定）
    model_config = {"frozen": False}
