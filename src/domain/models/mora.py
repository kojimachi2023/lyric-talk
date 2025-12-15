"""
Mora value object
モーラ（音節）を表す値オブジェクト
"""

import re
from typing import List

from pydantic import BaseModel


class Mora(BaseModel):
    """
    モーラ値オブジェクト

    モーラは日本語の音節単位を表す不変の値オブジェクトです。
    例: 「トウキョウ」→ [「ト」, 「ウ」, 「キョ」, 「ウ」]

    Attributes:
        value: モーラの文字列表現（カタカナ）
    """

    value: str

    model_config = {"frozen": True}  # 不変にする

    @staticmethod
    def split(katakana: str) -> List["Mora"]:
        """
        カタカナ文字列をモーラ単位で分割する

        モーラ分割のルール:
        - 拗音（キャ、シュ、チョ等）: 前の音と合わせて1モーラ
        - 促音（ッ）: 1モーラ
        - 撥音（ン）: 1モーラ
        - 長音（ー）: 1モーラ
        - 小さいァィゥェォ: 前の音と合わせて1モーラ（ファ、ティ等）

        Args:
            katakana: カタカナ文字列

        Returns:
            Moraオブジェクトのリスト

        Examples:
            >>> result = Mora.split("トウキョウ")
            >>> [m.value for m in result]
            ['ト', 'ウ', 'キョ', 'ウ']

            >>> result = Mora.split("ファイティング")
            >>> [m.value for m in result]
            ['ファ', 'イ', 'ティ', 'ン', 'グ']
        """
        if not katakana:
            return []

        # モーラ分割の正規表現パターン
        # 優先順位:
        # 1. 通常の文字 + 拗音・小文字 (長音は含めない)
        # 2. 単独の文字（ッ、ン、ー含む）
        mora_pattern = re.compile(
            r"[ァ-ヴヵヶ][ャュョァィゥェォ]?"  # 通常文字 + 拗音/小文字
            r"|[ッンー]"  # 単独の特殊文字
        )

        mora_strings = mora_pattern.findall(katakana)
        return [Mora(value=mora) for mora in mora_strings]
