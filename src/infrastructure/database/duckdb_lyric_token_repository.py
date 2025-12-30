"""DuckDB implementation of LyricTokenRepository."""

import json
from typing import List, Optional

import duckdb

from src.domain.models.lyric_token import LyricToken
from src.domain.models.reading import Reading
from src.domain.repositories.lyric_token_repository import LyricTokenRepository


class DuckDBLyricTokenRepository(LyricTokenRepository):
    """DuckDB implementation of LyricTokenRepository."""

    def __init__(self, connection: duckdb.DuckDBPyConnection):
        """Initialize repository with database connection.

        Args:
            connection: DuckDB database connection (injected by Unit of Work)
        """
        self._connection = connection

    def save(self, token: LyricToken) -> None:
        """Save a lyric token."""
        # Serialize moras to JSON
        moras_json = json.dumps([m.value for m in token.moras])

        self._connection.execute(
            """
            INSERT OR REPLACE INTO lyric_tokens
            (token_id, lyrics_corpus_id, surface, reading, lemma, pos,
             line_index, token_index, moras_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                token.token_id,
                token.lyrics_corpus_id,
                token.surface,
                token.reading.normalized,
                token.lemma,
                token.pos,
                token.line_index,
                token.token_index,
                moras_json,
            ],
        )

    def save_many(self, tokens: List[LyricToken]) -> None:
        """Save multiple lyric tokens."""
        if not tokens:
            return

        # Prepare data for batch insert
        data = []
        for token in tokens:
            moras_json = json.dumps([m.value for m in token.moras])
            data.append(
                (
                    token.token_id,
                    token.lyrics_corpus_id,
                    token.surface,
                    token.reading.normalized,
                    token.lemma,
                    token.pos,
                    token.line_index,
                    token.token_index,
                    moras_json,
                )
            )

        # Batch insert
        self._connection.executemany(
            """
            INSERT OR REPLACE INTO lyric_tokens
            (token_id, lyrics_corpus_id, surface, reading, lemma, pos,
             line_index, token_index, moras_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )

    def find_by_surface(self, surface: str, lyrics_corpus_id: str) -> List[LyricToken]:
        """Find lyric tokens by surface."""
        result = self._connection.execute(
            """
            SELECT token_id, lyrics_corpus_id, surface, reading, lemma, pos,
                   line_index, token_index, moras_json
            FROM lyric_tokens
            WHERE lyrics_corpus_id = ? AND surface = ?
            ORDER BY line_index, token_index
            """,
            [lyrics_corpus_id, surface],
        ).fetchall()

        return [self._row_to_token(row) for row in result]

    def find_by_reading(self, reading: str, lyrics_corpus_id: str) -> List[LyricToken]:
        """Find lyric tokens by reading."""
        result = self._connection.execute(
            """
            SELECT token_id, lyrics_corpus_id, surface, reading, lemma, pos,
                   line_index, token_index, moras_json
            FROM lyric_tokens
            WHERE lyrics_corpus_id = ? AND reading = ?
            ORDER BY line_index, token_index
            """,
            [lyrics_corpus_id, reading],
        ).fetchall()

        return [self._row_to_token(row) for row in result]

    def find_by_mora(self, mora: str, lyrics_corpus_id: str) -> List[LyricToken]:
        """Find lyric tokens containing the specified mora."""
        # Use DuckDB's JSON functions to filter at the SQL level
        # This avoids fetching all tokens and filtering in Python
        result = self._connection.execute(
            """
            SELECT token_id, lyrics_corpus_id, surface, reading, lemma, pos,
                   line_index, token_index, moras_json
            FROM lyric_tokens
            WHERE lyrics_corpus_id = ?
              AND list_contains(json_extract_string(moras_json, '$[*]')::VARCHAR[], ?)
            ORDER BY line_index, token_index
            """,
            [lyrics_corpus_id, mora],
        ).fetchall()

        return [self._row_to_token(row) for row in result]

    def find_by_token_id(self, token_id: str) -> Optional[LyricToken]:
        """Find a lyric token by token ID."""
        result = self._connection.execute(
            """
            SELECT token_id, lyrics_corpus_id, surface, reading, lemma, pos,
                   line_index, token_index, moras_json
            FROM lyric_tokens
            WHERE token_id = ?
            """,
            [token_id],
        ).fetchone()

        if result is None:
            return None

        return self._row_to_token(result)

    def find_by_token_ids(self, token_ids: List[str]) -> List[LyricToken]:
        """Find lyric tokens by multiple token IDs."""
        if not token_ids:
            return []

        # Create placeholders for IN clause
        placeholders = ",".join(["?" for _ in token_ids])
        query = f"""
            SELECT token_id, lyrics_corpus_id, surface, reading, lemma, pos,
                   line_index, token_index, moras_json
            FROM lyric_tokens
            WHERE token_id IN ({placeholders})
            ORDER BY line_index, token_index
        """

        result = self._connection.execute(query, token_ids).fetchall()

        return [self._row_to_token(row) for row in result]

    def has_mora(self, mora: str, lyrics_corpus_id: str) -> bool:
        """Check if any token in the corpus contains the specified mora."""
        # Use DuckDB's JSON functions and LIMIT 1 for early termination
        result = self._connection.execute(
            """
            SELECT 1
            FROM lyric_tokens
            WHERE lyrics_corpus_id = ?
              AND list_contains(json_extract_string(moras_json, '$[*]')::VARCHAR[], ?)
            LIMIT 1
            """,
            [lyrics_corpus_id, mora],
        ).fetchone()

        return result is not None

    def delete_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> None:
        """Delete all lyric tokens belonging to a lyrics corpus."""
        self._connection.execute(
            """
            DELETE FROM lyric_tokens
            WHERE lyrics_corpus_id = ?
            """,
            [lyrics_corpus_id],
        )

    def count_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> int:
        """Count tokens for a specific lyrics corpus.

        Args:
            lyrics_corpus_id: Lyrics corpus ID

        Returns:
            Number of tokens in the corpus
        """
        result = self._connection.execute(
            """
            SELECT COUNT(*)
            FROM lyric_tokens
            WHERE lyrics_corpus_id = ?
            """,
            [lyrics_corpus_id],
        ).fetchone()

        return result[0] if result else 0

    def list_by_lyrics_corpus_id(self, lyrics_corpus_id: str, limit: int) -> list[LyricToken]:
        """Get first N tokens for a specific corpus.

        Returns tokens ordered by line_index and token_index in ascending order.

        Args:
            lyrics_corpus_id: Lyrics corpus ID
            limit: Maximum number of tokens to return

        Returns:
            List of lyric tokens (ordered by position)
        """
        result = self._connection.execute(
            """
            SELECT token_id, lyrics_corpus_id, surface, reading,
                   lemma, pos, line_index, token_index, moras_json
            FROM lyric_tokens
            WHERE lyrics_corpus_id = ?
            ORDER BY line_index ASC, token_index ASC
            LIMIT ?
            """,
            [lyrics_corpus_id, limit],
        ).fetchall()

        return [self._row_to_token(row) for row in result]

    def _row_to_token(self, row) -> LyricToken:
        """Convert database row to LyricToken."""
        (
            token_id,
            lyrics_corpus_id,
            surface,
            reading,
            lemma,
            pos,
            line_index,
            token_index,
            moras_json,
        ) = row

        return LyricToken(
            lyrics_corpus_id=lyrics_corpus_id,
            surface=surface,
            reading=Reading(raw=reading),
            lemma=lemma,
            pos=pos,
            line_index=line_index,
            token_index=token_index,
        )
