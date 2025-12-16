"""
LyricToken entity
歌詞トークンを表すエンティティ
"""

from typing import List

from pydantic import BaseModel, computed_field

from src.domain.models.mora import Mora
from src.domain.models.reading import Reading


class LyricToken(BaseModel):
    """
    歌詞トークンエンティティ

    歌詞の形態素解析結果から得られる1つのトークン（単語）を表すエンティティです。
    エンティティなので可変（mutable）です。

    Attributes:
        lyrics_corpus_id: 歌詞コーパスのID
        surface: 表層形（実際の文字列）
        reading: 読み（Reading値オブジェクト）
        lemma: 基本形・見出し語
        pos: 品詞
        line_index: 行インデックス
        token_index: 行内のトークンインデックス
    """

    lyrics_corpus_id: str
    surface: str
    reading: Reading
    lemma: str
    pos: str
    line_index: int
    token_index: int

    # エンティティは可変なのでfrozen=Falseがデフォルト（明示的に設定不要）
    model_config = {"frozen": False}

    @computed_field  # type: ignore[misc]
    @property
    def token_id(self) -> str:
        """
        トークンの一意識別子

        フォーマット: {lyrics_corpus_id}_{line_index}_{token_index}

        Returns:
            トークンID文字列

        Examples:
            >>> token = LyricToken(
            ...     lyrics_corpus_id="corpus_001",
            ...     surface="東京",
            ...     reading=Reading(raw="とうきょう"),
            ...     lemma="東京",
            ...     pos="名詞",
            ...     line_index=2,
            ...     token_index=3
            ... )
            >>> token.token_id
            'corpus_001_2_3'
        """
        return f"{self.lyrics_corpus_id}_{self.line_index}_{self.token_index}"

    @computed_field  # type: ignore[misc]
    @property
    def moras(self) -> List[Mora]:
        """
        トークンの読みをモーラ単位に分割

        Reading値オブジェクトの読みをモーラのリストに変換します。

        Returns:
            Moraオブジェクトのリスト

        Examples:
            >>> token = LyricToken(
            ...     lyrics_corpus_id="corpus_001",
            ...     surface="東京",
            ...     reading=Reading(raw="とうきょう"),
            ...     lemma="東京",
            ...     pos="名詞",
            ...     line_index=0,
            ...     token_index=0
            ... )
            >>> [m.value for m in token.moras]
            ['ト', 'ウ', 'キョ', 'ウ']
        """
        return self.reading.to_moras()
