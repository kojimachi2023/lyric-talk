"""
MatchResult value object and related types
マッチング結果を表す値オブジェクト
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MatchType(str, Enum):
    """
    マッチングの種類を表す列挙型

    Attributes:
        EXACT_SURFACE: 表層形の完全一致
        EXACT_READING: 読みの完全一致
        MORA_COMBINATION: モーラの組み合わせによる一致
        NO_MATCH: 一致なし
    """

    EXACT_SURFACE = "exact_surface"
    EXACT_READING = "exact_reading"
    MORA_COMBINATION = "mora_combination"
    NO_MATCH = "no_match"


class MoraMatchDetail(BaseModel):
    """
    モーラマッチの詳細を表す値オブジェクト

    モーラ組み合わせマッチング時に、各モーラがどのトークンから
    取得されたかを記録します。

    Attributes:
        mora: モーラ文字列（例: "ト", "キョ"）
        source_token_id: モーラの取得元トークンID
        mora_index: トークン内でのモーラのインデックス
    """

    mora: str
    source_token_id: str
    mora_index: int

    model_config = {"frozen": True}  # 値オブジェクトなので不変


class MatchResult(BaseModel):
    """
    マッチング結果を表す値オブジェクト

    入力トークンに対するマッチング結果を表します。
    マッチタイプ、一致したトークンID、モーラ詳細などを含みます。

    Attributes:
        input_token: 入力トークン（表層形）
        input_reading: 入力トークンの読み（カタカナ）
        match_type: マッチングの種類
        matched_token_ids: 一致した歌詞トークンのIDリスト
        mora_details: モーラマッチの詳細（MORA_COMBINATIONの場合）
    """

    input_token: str
    input_reading: str
    match_type: MatchType
    matched_token_ids: List[str] = Field(default_factory=list)
    mora_details: Optional[List[MoraMatchDetail]] = None

    model_config = {"frozen": True}  # 値オブジェクトなので不変
