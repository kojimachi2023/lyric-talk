"""
モーラ分割ユーティリティ
カタカナ文字列をモーラ（音節）単位で分割する
"""

import re


def split_mora(katakana: str) -> list[str]:
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
        モーラのリスト

    Examples:
        >>> split_mora("トウキョウ")
        ['ト', 'ウ', 'キョ', 'ウ']
        >>> split_mora("ファイティング")
        ['ファ', 'イ', 'ティ', 'ン', 'グ']
    """
    if not katakana:
        return []

    # モーラ分割の正規表現パターン
    # 優先順位:
    # 1. 通常の文字 + 拗音・小文字 + 長音（オプション）
    # 2. 単独の文字（ッ、ン、ー含む）
    mora_pattern = re.compile(
        r"[ァ-ヴヵヶ][ャュョァィゥェォ]?ー?"  # 通常文字 + 拗音/小文字 + 長音
        r"|[ッンー]"  # 単独の特殊文字
    )

    moras = mora_pattern.findall(katakana)
    return moras


def hiragana_to_katakana(hiragana: str) -> str:
    """
    ひらがなをカタカナに変換する

    Args:
        hiragana: ひらがな文字列

    Returns:
        カタカナ文字列
    """
    return "".join(chr(ord(char) + 96) if "ぁ" <= char <= "ゖ" else char for char in hiragana)


def katakana_to_hiragana(katakana: str) -> str:
    """
    カタカナをひらがなに変換する

    Args:
        katakana: カタカナ文字列

    Returns:
        ひらがな文字列
    """
    return "".join(chr(ord(char) - 96) if "ァ" <= char <= "ヶ" else char for char in katakana)


def normalize_reading(reading: str) -> str:
    """
    読みを正規化する（カタカナに統一）

    Args:
        reading: 読み文字列（ひらがなまたはカタカナ）

    Returns:
        カタカナに統一された読み
    """
    return hiragana_to_katakana(reading)
