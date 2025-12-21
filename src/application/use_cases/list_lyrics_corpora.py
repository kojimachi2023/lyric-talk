"""
Application Use Case: List Lyrics Corpora
歌詞コーパス一覧取得ユースケース
"""

from src.application.dtos.cli_summaries import LyricsCorpusSummaryDto
from src.domain.repositories.lyric_token_repository import LyricTokenRepository
from src.domain.repositories.lyrics_repository import LyricsRepository


class ListLyricsCorporaUseCase:
    """
    歌詞コーパス一覧取得ユースケース

    保存されている歌詞コーパスの一覧をサマリー情報として取得する。
    CLI の対話選択機能で使用するための概要情報を提供。
    """

    def __init__(
        self,
        lyrics_repository: LyricsRepository,
        lyric_token_repository: LyricTokenRepository,
    ):
        """
        コンストラクタ

        Args:
            lyrics_repository: 歌詞コーパスリポジトリ
            lyric_token_repository: 歌詞トークンリポジトリ
        """
        self._lyrics_repository = lyrics_repository
        self._lyric_token_repository = lyric_token_repository

    def execute(self, limit: int = 10, max_preview_token: int = 10) -> list[LyricsCorpusSummaryDto]:
        """
        歌詞コーパス一覧を取得する

        Args:
            limit: 取得する最大件数（デフォルト: 10）
            max_preview_token: プレビュー用に取得する最大トークン数（デフォルト: 10）

        Returns:
            歌詞コーパスサマリーDTOのリスト（新しい順）
        """
        # 最新のコーパス一覧を取得
        corpora = self._lyrics_repository.list_lyrics_corpora(limit)

        # 各コーパスのサマリー情報を構築
        summaries: list[LyricsCorpusSummaryDto] = []
        for corpus in corpora:
            # トークン数を取得
            token_count = self._lyric_token_repository.count_by_lyrics_corpus_id(
                corpus.lyrics_corpus_id
            )

            # プレビュー用のトークンを取得
            preview_tokens = self._lyric_token_repository.list_by_lyrics_corpus_id(
                corpus.lyrics_corpus_id, limit=max_preview_token
            )

            # プレビューテキストを生成（トークンのsurfaceを連結）
            preview_text = "".join(token.surface for token in preview_tokens)

            # DTOを作成
            summary = LyricsCorpusSummaryDto(
                lyrics_corpus_id=corpus.lyrics_corpus_id,
                title=corpus.title,
                artist=corpus.artist,
                created_at=corpus.created_at,
                token_count=token_count,
                preview_text=preview_text,
            )
            summaries.append(summary)

        return summaries
