"""
Unit of Work interface (Port)
トランザクション管理のためのUnit of Workパターン
"""

from abc import ABC, abstractmethod

from src.domain.repositories.lyric_token_repository import LyricTokenRepository
from src.domain.repositories.lyrics_repository import LyricsRepository
from src.domain.repositories.match_repository import MatchRepository


class UnitOfWork(ABC):
    """
    Unit of Workインターフェース

    複数のリポジトリにまたがる操作を単一のトランザクション内で
    実行するためのパターン。コンテキストマネージャとして使用する。

    Usage:
        with unit_of_work as uow:
            uow.lyrics_repository.save(corpus)
            uow.lyric_token_repository.save_many(tokens)
            uow.commit()
    """

    lyrics_repository: LyricsRepository
    lyric_token_repository: LyricTokenRepository
    match_repository: MatchRepository

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        """トランザクションを開始する"""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        コンテキスト終了時の処理

        例外が発生した場合は自動的にロールバックする。
        commit()が呼ばれていない場合、変更は破棄される。
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """トランザクションをコミットする"""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """トランザクションをロールバックする"""
        pass
