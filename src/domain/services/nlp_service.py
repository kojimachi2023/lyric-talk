"""
NlpService Port interface
NLP処理を抽象化したサービスインターフェース
"""

from abc import ABC, abstractmethod
from typing import List

from src.application.dtos.token_data import TokenData


class NlpService(ABC):
    """
    NLP処理サービスのインターフェース

    テキストのトークン化・形態素解析を抽象化したインターフェース。
    実装はInfrastructure層で行う（SpaCy + GiNZA等）。
    """

    @abstractmethod
    def tokenize(self, text: str) -> List[TokenData]:
        """
        テキストをトークン化する

        形態素解析を行い、表層形・読み・品詞などの情報を取得する。

        Args:
            text: トークン化するテキスト

        Returns:
            TokenDataのリスト
        """
        pass
