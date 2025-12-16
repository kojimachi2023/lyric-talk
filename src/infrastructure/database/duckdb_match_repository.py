"""DuckDB implementation of MatchRepository."""

import json
import uuid
from typing import List, Optional

import duckdb

from src.domain.models.match_result import MatchResult, MatchType, MoraMatchDetail
from src.domain.models.match_run import MatchRun
from src.domain.repositories.match_repository import MatchRepository


class DuckDBMatchRepository(MatchRepository):
    """DuckDB implementation of MatchRepository."""

    def __init__(self, db_path: str):
        """Initialize repository with database path.

        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get database connection."""
        return duckdb.connect(self.db_path)

    def save_run(self, match_run: MatchRun) -> None:
        """Save a match run."""
        conn = self._get_connection()
        try:
            config_json = json.dumps(match_run.config)

            conn.execute(
                """
                INSERT OR REPLACE INTO match_runs
                (run_id, lyrics_corpus_id, input_text, timestamp, config_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    match_run.run_id,
                    match_run.lyrics_corpus_id,
                    match_run.input_text,
                    match_run.timestamp,
                    config_json,
                ],
            )
        finally:
            conn.close()

    def save_results(self, run_id: str, results: List[MatchResult]) -> None:
        """Save match results."""
        if not results:
            return

        conn = self._get_connection()
        try:
            # Prepare data for batch insert
            data = []
            for result in results:
                result_id = str(uuid.uuid4())
                matched_token_ids_json = json.dumps(result.matched_token_ids)
                mora_details_json = json.dumps(
                    [
                        {
                            "mora": d.mora,
                            "source_token_id": d.source_token_id,
                            "mora_index": d.mora_index,
                        }
                        for d in result.mora_details
                    ]
                    if result.mora_details
                    else []
                )

                # Get first token_id if available (for foreign key)
                token_id = result.matched_token_ids[0] if result.matched_token_ids else None

                data.append(
                    (
                        result_id,
                        run_id,
                        token_id,
                        result.input_token,
                        result.input_reading,
                        result.match_type.value,
                        matched_token_ids_json,
                        mora_details_json,
                    )
                )

            # Batch insert
            conn.executemany(
                """
                INSERT INTO match_results
                (result_id, run_id, token_id, input_token, input_reading,
                 match_type, matched_token_ids_json, mora_details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                data,
            )
        finally:
            conn.close()

    def find_run_by_id(self, run_id: str) -> Optional[MatchRun]:
        """Find a match run by ID."""
        conn = self._get_connection()
        try:
            result = conn.execute(
                """
                SELECT run_id, lyrics_corpus_id, input_text, timestamp, config_json
                FROM match_runs
                WHERE run_id = ?
                """,
                [run_id],
            ).fetchone()

            if result is None:
                return None

            return self._row_to_run(result)
        finally:
            conn.close()

    def find_results_by_run_id(self, run_id: str) -> List[MatchResult]:
        """Find match results by run ID."""
        conn = self._get_connection()
        try:
            result = conn.execute(
                """
                SELECT result_id, run_id, token_id, input_token, input_reading,
                       match_type, matched_token_ids_json, mora_details_json
                FROM match_results
                WHERE run_id = ?
                ORDER BY result_id
                """,
                [run_id],
            ).fetchall()

            return [self._row_to_result(row) for row in result]
        finally:
            conn.close()

    def find_runs_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> List[MatchRun]:
        """Find match runs by lyrics corpus ID."""
        conn = self._get_connection()
        try:
            result = conn.execute(
                """
                SELECT run_id, lyrics_corpus_id, input_text, timestamp, config_json
                FROM match_runs
                WHERE lyrics_corpus_id = ?
                ORDER BY timestamp DESC
                """,
                [lyrics_corpus_id],
            ).fetchall()

            return [self._row_to_run(row) for row in result]
        finally:
            conn.close()

    def delete_run(self, run_id: str) -> None:
        """Delete a match run and its results."""
        conn = self._get_connection()
        try:
            # Delete results first (foreign key constraint)
            conn.execute(
                """
                DELETE FROM match_results
                WHERE run_id = ?
                """,
                [run_id],
            )

            # Delete run
            conn.execute(
                """
                DELETE FROM match_runs
                WHERE run_id = ?
                """,
                [run_id],
            )
        finally:
            conn.close()

    def _row_to_run(self, row) -> MatchRun:
        """Convert database row to MatchRun."""
        run_id, lyrics_corpus_id, input_text, timestamp, config_json = row

        config = json.loads(config_json)

        return MatchRun(
            run_id=run_id,
            lyrics_corpus_id=lyrics_corpus_id,
            input_text=input_text,
            timestamp=timestamp,
            config=config,
        )

    def _row_to_result(self, row) -> MatchResult:
        """Convert database row to MatchResult."""
        (
            result_id,
            run_id,
            token_id,
            input_token,
            input_reading,
            match_type,
            matched_token_ids_json,
            mora_details_json,
        ) = row

        matched_token_ids = json.loads(matched_token_ids_json)
        mora_details_data = json.loads(mora_details_json)

        mora_details = [
            MoraMatchDetail(
                mora=d["mora"],
                source_token_id=d["source_token_id"],
                mora_index=d["mora_index"],
            )
            for d in mora_details_data
        ]

        return MatchResult(
            input_token=input_token,
            input_reading=input_reading,
            match_type=MatchType(match_type),
            matched_token_ids=matched_token_ids,
            mora_details=mora_details,
        )
