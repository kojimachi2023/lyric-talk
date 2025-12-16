"""
LyricsCorpus entity
歌詞コーパスを表すエンティティ
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LyricsCorpus(BaseModel):
    """
    歌詞コーパスエンティティ

    歌詞コーパス全体のメタデータを管理するエンティティです。
    実際の歌詞トークンは LyricToken エンティティとして別途管理されます。
    エンティティなので可変（mutable）です。

    Attributes:
        lyrics_corpus_id: 歌詞コーパスの一意識別子（UUID推奨）
        content_hash: 歌詞テキストのSHA256ハッシュ（重複チェック用）
        title: 歌詞のタイトル（オプション）
        created_at: 作成日時
    """

    lyrics_corpus_id: str
    content_hash: str
    title: Optional[str] = None
    created_at: datetime

    # エンティティは可変なのでfrozen=Falseがデフォルト（明示的に設定）
    model_config = {"frozen": False}
