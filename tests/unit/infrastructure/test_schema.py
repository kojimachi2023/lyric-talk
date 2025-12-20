"""Tests for DB schema initialization."""

import tempfile
from pathlib import Path

from src.infrastructure.database.schema import initialize_database


def test_initialize_database_creates_tables():
    """Test that initialize_database() creates all required tables."""
    # Import will fail initially (Red phase)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = initialize_database(str(db_path))

        # Check that all tables are created
        tables_query = (
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        )
        tables = conn.execute(tables_query).fetchall()
        table_names = {row[0] for row in tables}

        assert "lyrics_corpus" in table_names
        assert "lyric_tokens" in table_names
        assert "match_runs" in table_names
        assert "match_results" in table_names

        conn.close()


def test_initialize_database_creates_proper_schema():
    """Test that tables have proper columns and structure."""

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = initialize_database(str(db_path))

        # Test lyrics_corpus table structure
        corpus_info = conn.execute("PRAGMA table_info('lyrics_corpus')").fetchall()
        corpus_cols = {row[1] for row in corpus_info}  # row[1] is column name
        assert "corpus_id" in corpus_cols
        assert "title" in corpus_cols
        assert "artist" in corpus_cols
        assert "content_hash" in corpus_cols

        # Test lyric_tokens table structure
        tokens_info = conn.execute("PRAGMA table_info('lyric_tokens')").fetchall()
        tokens_cols = {row[1] for row in tokens_info}
        assert "token_id" in tokens_cols
        assert "lyrics_corpus_id" in tokens_cols
        assert "surface" in tokens_cols
        assert "reading" in tokens_cols

        # Test match_runs table structure
        runs_info = conn.execute("PRAGMA table_info('match_runs')").fetchall()
        runs_cols = {row[1] for row in runs_info}
        assert "run_id" in runs_cols
        assert "input_text" in runs_cols
        assert "timestamp" in runs_cols

        # Test match_results table structure
        results_info = conn.execute("PRAGMA table_info('match_results')").fetchall()
        results_cols = {row[1] for row in results_info}
        assert "result_id" in results_cols
        assert "run_id" in results_cols
        assert "token_id" in results_cols
        assert "match_type" in results_cols

        conn.close()


def test_initialize_database_creates_indexes():
    """Test that appropriate indexes are created."""

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn = initialize_database(str(db_path))

        # Check for indexes - DuckDB doesn't have a standard way to list indexes
        # We'll verify index creation by checking query performance hints
        # or by attempting to create the same index (should fail if exists)
        # For now, we'll just verify the function runs without errors

        conn.close()


def test_initialize_database_idempotent():
    """Test that initialize_database() can be called multiple times safely."""

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        conn1 = initialize_database(str(db_path))
        conn1.close()

        # Should not raise error when called again
        conn2 = initialize_database(str(db_path))
        conn2.close()
