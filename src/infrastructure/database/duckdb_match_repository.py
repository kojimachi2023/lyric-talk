"""DuckDB implementation of MatchRepository."""

import json
import uuid
from typing import List, Optional

import duckdb

from src.domain.models.match_result import MatchResult, MatchType, MoraMatchDetail
from src.domain.models.match_run import MatchRun
from src.domain.repositories.match_repository import MatchRepository


class DuckDBMatchRepository(MatchRepository):
    """DuckDB implementation of MatchRepository.

    集約パターンに従い、MatchRun（集約ルート）とその子エンティティである
    MatchResultを一括で保存・取得する。
    """

    def __init__(self, connection: duckdb.DuckDBPyConnection):
        """Initialize repository with database connection.

        Args:
            connection: DuckDB database connection (injected by Unit of Work)
        """
        self._connection = connection

    def save(self, match_run: MatchRun) -> str:
        """Save a match run with its results (aggregate).

        集約全体（MatchRun + MatchResult）をトランザクション内で保存する。
        """
        config_json = json.dumps(match_run.config)

        # Save MatchRun
        self._connection.execute(
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

        # Save MatchResults (child entities)
        if match_run.results:
            self._save_results(match_run.run_id, match_run.results)

        return match_run.run_id

    def _save_results(self, run_id: str, results: List[MatchResult]) -> None:
        """Save match results to database (internal method)."""
        if not results:
            return

        # Prepare data for batch insert
        data = []
        for idx, result in enumerate(results):
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

            # Use array index as input_token_index
            input_token_index = idx

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
                    input_token_index,
                )
            )

        # Batch insert
        self._connection.executemany(
            """
            INSERT INTO match_results
            (result_id, run_id, token_id, input_token, input_reading,
             match_type, matched_token_ids_json, mora_details_json, input_token_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )

    def find_by_id(self, run_id: str) -> Optional[MatchRun]:
        """Find a match run by ID with its results."""
        # Get MatchRun
        run_row = self._connection.execute(
            """
            SELECT run_id, lyrics_corpus_id, input_text, timestamp, config_json
            FROM match_runs
            WHERE run_id = ?
            """,
            [run_id],
        ).fetchone()

        if run_row is None:
            return None

        # Get MatchResults
        result_rows = self._connection.execute(
            """
            SELECT result_id, run_id, token_id, input_token, input_reading,
                   match_type, matched_token_ids_json, mora_details_json, input_token_index
            FROM match_results
            WHERE run_id = ?
            ORDER BY input_token_index, result_id
            """,
            [run_id],
        ).fetchall()

        results = [self._row_to_result(row) for row in result_rows]
        return self._row_to_run(run_row, results)

    def find_by_lyrics_corpus_id(self, lyrics_corpus_id: str) -> List[MatchRun]:
        """Find match runs by lyrics corpus ID with their results."""
        run_rows = self._connection.execute(
            """
            SELECT run_id, lyrics_corpus_id, input_text, timestamp, config_json
            FROM match_runs
            WHERE lyrics_corpus_id = ?
            ORDER BY timestamp DESC
            """,
            [lyrics_corpus_id],
        ).fetchall()

        runs = []
        for run_row in run_rows:
            run_id = run_row[0]
            result_rows = self._connection.execute(
                """
                SELECT result_id, run_id, token_id, input_token, input_reading,
                       match_type, matched_token_ids_json, mora_details_json, input_token_index
                FROM match_results
                WHERE run_id = ?
                ORDER BY input_token_index, result_id
                """,
                [run_id],
            ).fetchall()
            results = [self._row_to_result(row) for row in result_rows]
            runs.append(self._row_to_run(run_row, results))

        return runs

    def delete(self, run_id: str) -> None:
        """Delete a match run and its results."""
        # Delete results first (foreign key constraint)
        self._connection.execute(
            """
            DELETE FROM match_results
            WHERE run_id = ?
            """,
            [run_id],
        )

        # Delete run
        self._connection.execute(
            """
            DELETE FROM match_runs
            WHERE run_id = ?
            """,
            [run_id],
        )

    def _row_to_run(self, row, results: List[MatchResult] = None) -> MatchRun:
        """Convert database row to MatchRun with results."""
        run_id, lyrics_corpus_id, input_text, timestamp, config_json = row

        config = json.loads(config_json)

        return MatchRun(
            run_id=run_id,
            lyrics_corpus_id=lyrics_corpus_id,
            input_text=input_text,
            timestamp=timestamp,
            config=config,
            results=results or [],
        )

    def list_match_runs(self, limit: int) -> list[MatchRun]:
        """Get recent match runs list.

        Returns runs ordered by timestamp in descending order (newest first).

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of match runs (newest first, with results included)
        """
        # Get runs ordered by timestamp
        runs_rows = self._connection.execute(
            """
            SELECT run_id, lyrics_corpus_id, input_text, timestamp, config_json
            FROM match_runs
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()

        runs = []
        for run_row in runs_rows:
            run_id, lyrics_corpus_id, input_text, timestamp, config_json = run_row
            config = json.loads(config_json)

            # Get results for this run
            results_rows = self._connection.execute(
                """
                SELECT result_id, run_id, token_id, input_token,
                       input_reading, match_type, matched_token_ids_json,
                       mora_details_json, input_token_index
                FROM match_results
                WHERE run_id = ?
                ORDER BY input_token_index
                """,
                [run_id],
            ).fetchall()

            results = [self._row_to_result(row) for row in results_rows]

            run = MatchRun(
                run_id=run_id,
                lyrics_corpus_id=lyrics_corpus_id,
                input_text=input_text,
                timestamp=timestamp,
                config=config,
                results=results,
            )
            runs.append(run)

        return runs

    def _row_to_result(self, row) -> MatchResult:
        """Convert database row to MatchResult (immutable value object)."""
        (
            result_id,
            run_id,
            token_id,
            input_token,
            input_reading,
            match_type,
            matched_token_ids_json,
            mora_details_json,
            input_token_index,
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
            mora_details=mora_details if mora_details else None,
        )
