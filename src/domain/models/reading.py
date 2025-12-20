"""
Reading value object
読みを表す値オブジェクト
"""

from typing import List

from pydantic import BaseModel, computed_field

from src.domain.models.mora import Mora


class Reading(BaseModel):
    """
    読み値オブジェクト

    読みは、ひらがなまたはカタカナで表現される発音情報です。
    内部的にはカタカナに正規化され、モーラ単位に分割できます。

    Attributes:
        raw: 元の読み文字列（ひらがなまたはカタカナ）
    """

    raw: str

    model_config = {"frozen": True}  # 不変にする

    @computed_field  # type: ignore[misc]
    @property
    def normalized(self) -> str:
        """
        正規化された読み（カタカナ）

        ひらがなをカタカナに変換して正規化します。
        すでにカタカナの場合はそのまま返します。

        Returns:
            カタカナに統一された読み文字列
        """
        return self._hiragana_to_katakana(self.raw)

    def to_moras(self) -> List[Mora]:
        """
        読みをモーラのリストに分割する

        正規化された読み（カタカナ）をモーラ単位に分割します。

        Returns:
            Moraオブジェクトのリスト
        """
        return Mora.split(self.normalized)

    @staticmethod
    def _hiragana_to_katakana(text: str) -> str:
        """
        ひらがなをカタカナに変換する

        Args:
            text: 変換対象の文字列

        Returns:
            カタカナに変換された文字列
        """
        return "".join(chr(ord(char) + 96) if "ぁ" <= char <= "ゖ" else char for char in text)
