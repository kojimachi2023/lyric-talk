"""
Application DTOs (Data Transfer Objects)
アプリケーション層で使用するデータ転送オブジェクト
"""

from pydantic import BaseModel


class TokenData(BaseModel):
    """
    NLP処理結果のトークンデータ DTO

    NlpServiceからアプリケーション層に返されるトークンの情報。
    ドメインモデルに変換される前の中間データ構造。

    Attributes:
        surface: 表層形（実際の文字列）
        reading: 読み（ひらがな or カタカナ）
        lemma: 基本形・見出し語
        pos: 品詞
    """

    surface: str
    reading: str
    lemma: str
    pos: str

    model_config = {"frozen": True}  # DTOは不変
