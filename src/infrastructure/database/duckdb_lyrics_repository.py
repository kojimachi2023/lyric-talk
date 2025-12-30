"""DuckDB implementation of LyricsRepository."""

from typing import Optional

import duckdb

from src.domain.models.lyrics_corpus import LyricsCorpus
from src.domain.repositories.lyrics_repository import LyricsRepository


class DuckDBLyricsRepository(LyricsRepository):
    """DuckDB implementation of LyricsRepository."""

    def __init__(self, connection: duckdb.DuckDBPyConnection):
        """Initialize repository with database connection.

        Args:
            connection: DuckDB database connection (injected by Unit of Work)
        """
        self._connection = connection

    def save(self, lyrics_corpus: LyricsCorpus) -> str:
        """Save a lyrics corpus."""
        self._connection.execute(
            """
            INSERT INTO lyrics_corpus
            (corpus_id, title, artist, content_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (corpus_id) DO UPDATE SET
                title = excluded.title,
                artist = excluded.artist,
                content_hash = excluded.content_hash,
                created_at = excluded.created_at
            """,
            [
                lyrics_corpus.lyrics_corpus_id,
                lyrics_corpus.title,
                lyrics_corpus.artist,
                lyrics_corpus.content_hash,
                lyrics_corpus.created_at,
            ],
        )
        return lyrics_corpus.lyrics_corpus_id

    def find_by_id(self, lyrics_corpus_id: str) -> Optional[LyricsCorpus]:
        """Find a lyrics corpus by ID."""
        result = self._connection.execute(
            """
            SELECT corpus_id, title, artist, content_hash, created_at
            FROM lyrics_corpus
            WHERE corpus_id = ?
            """,
            [lyrics_corpus_id],
        ).fetchone()

        if result is None:
            return None

        return self._row_to_corpus(result)

    def find_by_content_hash(self, content_hash: str) -> Optional[LyricsCorpus]:
        """Find a lyrics corpus by content hash."""
        result = self._connection.execute(
            """
            SELECT corpus_id, title, artist, content_hash, created_at
            FROM lyrics_corpus
            WHERE content_hash = ?
            """,
            [content_hash],
        ).fetchone()

        if result is None:
            return None

        return self._row_to_corpus(result)

    def find_by_title(self, title: str) -> list[LyricsCorpus]:
        """Find lyrics corpora by title (partial match)."""
        result = self._connection.execute(
            """
            SELECT corpus_id, title, artist, content_hash, created_at
            FROM lyrics_corpus
            WHERE title LIKE ?
            ORDER BY created_at DESC
            """,
            [f"%{title}%"],
        ).fetchall()

        return [self._row_to_corpus(row) for row in result]

    def delete(self, lyrics_corpus_id: str) -> None:
        """Delete a lyrics corpus."""
        # Delete associated tokens first (foreign key constraint)
        self._connection.execute(
            """
            DELETE FROM lyric_tokens
            WHERE lyrics_corpus_id = ?
            """,
            [lyrics_corpus_id],
        )

        # Delete corpus
        self._connection.execute(
            """
            DELETE FROM lyrics_corpus
            WHERE corpus_id = ?
            """,
            [lyrics_corpus_id],
        )

    def list_lyrics_corpora(self, limit: int) -> list[LyricsCorpus]:
        """Get lyrics corpus list.

        Returns corpora ordered by created_at in descending order (newest first).

        Args:
            limit: Maximum number of corpora to return

        Returns:
            List of lyrics corpora (newest first)
        """
        result = self._connection.execute(
            """
            SELECT corpus_id, title, artist, content_hash, created_at
            FROM lyrics_corpus
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()

        return [self._row_to_corpus(row) for row in result]

    def _row_to_corpus(self, row) -> LyricsCorpus:
        """Convert database row to LyricsCorpus."""
        corpus_id, title, artist, content_hash, created_at = row

        return LyricsCorpus(
            lyrics_corpus_id=corpus_id,
            title=title,
            artist=artist,
            content_hash=content_hash,
            created_at=created_at,
        )
