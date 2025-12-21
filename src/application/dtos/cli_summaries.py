"""
Application DTOs for CLI display
CLI表示用のサマリーデータ転送オブジェクト
"""

from datetime import datetime

from pydantic import BaseModel


class LyricsCorpusSummaryDto(BaseModel):
    """
    歌詞コーパスのサマリー情報 DTO

    CLI一覧表示やインタラクティブ選択で使用する概要情報。
    詳細情報を含まないため、パフォーマンス最適化が可能。

    Attributes:
        lyrics_corpus_id: コーパスの一意識別子
        title: 曲のタイトル（任意）
        artist: アーティスト名（任意）
        created_at: コーパス作成日時
        token_count: コーパスに含まれるトークン数
        preview_text: プレビュー用のテキスト（先頭Nトークンの連結）
    """

    lyrics_corpus_id: str
    title: str | None
    artist: str | None
    created_at: datetime
    token_count: int
    preview_text: str

    model_config = {"frozen": True}


class MatchRunSummaryDto(BaseModel):
    """
    マッチング実行履歴のサマリー情報 DTO

    CLI一覧表示やインタラクティブ選択で使用する概要情報。

    Attributes:
        run_id: 実行の一意識別子
        lyrics_corpus_id: 対象となったコーパスID
        timestamp: 実行日時
        input_text: マッチング対象として入力されたテキスト（全文）
        results_count: マッチング結果の件数
    """

    run_id: str
    lyrics_corpus_id: str
    timestamp: datetime
    input_text: str
    results_count: int

    model_config = {"frozen": True}
