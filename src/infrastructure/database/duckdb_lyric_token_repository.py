"""DuckDB implementation of LyricTokenRepository."""

import json
from typing import List, Optional

import duckdb

from src.domain.models.lyric_token import LyricToken
from src.domain.models.reading import Reading
from src.domain.repositories.lyric_token_repository import LyricTokenRepository


class DuckDBLyricTokenRepository(LyricTokenRepository):
    """DuckDB implementation of LyricTokenRepository."""

    def __init__(self, db_path: str):
        """Initialize repository with database path.

        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get database connection."""
        return duckdb.connect(self.db_path)

    def save(self, token: LyricToken) -> None:
        """Save a lyric token."""
        conn = self._get_connection()
        try:
            # Serialize moras to JSON
            moras_json = json.dumps([m.value for m in token.moras])

            conn.execute(
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
        finally:
            conn.close()

    def save_many(self, tokens: List[LyricToken]) -> None:
        """Save multiple lyric tokens."""
        if not tokens:
            return

        conn = self._get_connection()
        try:
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
            conn.executemany(
                """
                INSERT OR REPLACE INTO lyric_tokens
                (token_id, lyrics_corpus_id, surface, reading, lemma, pos,
                 line_index, token_index, moras_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                data,
            )
        finally:
            conn.close()

    def find_by_surface(self, surface: str, lyrics_corpus_id: str) -> List[LyricToken]:
        """Find lyric tokens by surface."""
        conn = self._get_connection()
        try:
            result = conn.execute(
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
        finally:
            conn.close()

    def find_by_reading(self, reading: str, lyrics_corpus_id: str) -> List[LyricToken]:
        """Find lyric tokens by reading."""
        conn = self._get_connection()
        try:
            result = conn.execute(
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
        finally:
            conn.close()

    def find_by_mora(self, mora: str, lyrics_corpus_id: str) -> List[LyricToken]:
        """Find lyric tokens containing the specified mora."""
        conn = self._get_connection()
        try:
            # Use json_array_length and json_array_get to search within JSON array
            # Get all tokens and filter in Python for simplicity
            result = conn.execute(
                """
                SELECT token_id, lyrics_corpus_id, surface, reading, lemma, pos,
                       line_index, token_index, moras_json
                FROM lyric_tokens
                WHERE lyrics_corpus_id = ?
                ORDER BY line_index, token_index
                """,
                [lyrics_corpus_id],
            ).fetchall()

            # Filter in Python to check if mora exists in JSON array
            filtered_results = []
            for row in result:
                moras_json = row[8]  # moras_json column
                if mora in json.loads(moras_json):
                    filtered_results.append(self._row_to_token(row))

            return filtered_results
        finally:
            conn.close()

    def find_by_token_id(self, token_id: str) -> Optional[LyricToken]:
        """Find a lyric token by token ID."""
        conn = self._get_connection()
        try:
            result = conn.execute(
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
        finally:
            conn.close()

    def find_by_token_ids(self, token_ids: List[str]) -> List[LyricToken]:
        """Find lyric tokens by multiple token IDs."""
        if not token_ids:
            return []

        conn = self._get_connection()
        try:
            # Create placeholders for IN clause
            placeholders = ",".join(["?" for _ in token_ids])
            query = f"""
                SELECT token_id, lyrics_corpus_id, surface, reading, lemma, pos,
                       line_index, token_index, moras_json
                FROM lyric_tokens
                WHERE token_id IN ({placeholders})
                ORDER BY line_index, token_index
            """

            result = conn.execute(query, token_ids).fetchall()

            return [self._row_to_token(row) for row in result]
        finally:
            conn.close()

    def has_mora(self, mora: str, lyrics_corpus_id: str) -> bool:
        """Check if any token in the corpus contains the specified mora."""
        conn = self._get_connection()
        try:
            # Get all tokens and check if any contains the mora
            result = conn.execute(
                """
                SELECT moras_json
                FROM lyric_tokens
                WHERE lyrics_corpus_id = ?
                """,
                [lyrics_corpus_id],
            ).fetchall()

            # Check in Python
            for row in result:
                moras_json = row[0]
                if mora in json.loads(moras_json):
                    return True

            return False
        finally:
            conn.close()

    def delete_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> None:
        """Delete all lyric tokens belonging to a lyrics corpus."""
        conn = self._get_connection()
        try:
            conn.execute(
                """
                DELETE FROM lyric_tokens
                WHERE lyrics_corpus_id = ?
                """,
                [lyrics_corpus_id],
            )
        finally:
            conn.close()

    def count_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> int:
        """Count tokens for a specific lyrics corpus.

        Args:
            lyrics_corpus_id: Lyrics corpus ID

        Returns:
            Number of tokens in the corpus
        """
        conn = self._get_connection()
        try:
            result = conn.execute(
                """
                SELECT COUNT(*)
                FROM lyric_tokens
                WHERE lyrics_corpus_id = ?
                """,
                [lyrics_corpus_id],
            ).fetchone()

            return result[0] if result else 0
        finally:
            conn.close()

    def list_by_lyrics_corpus_id(self, lyrics_corpus_id: str, limit: int) -> list[LyricToken]:
        """Get first N tokens for a specific corpus.

        Returns tokens ordered by line_index and token_index in ascending order.

        Args:
            lyrics_corpus_id: Lyrics corpus ID
            limit: Maximum number of tokens to return

        Returns:
            List of lyric tokens (ordered by position)
        """
        conn = self._get_connection()
        try:
            result = conn.execute(
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
        finally:
            conn.close()

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
