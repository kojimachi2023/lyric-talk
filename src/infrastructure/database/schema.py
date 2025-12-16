"""Database schema for DuckDB."""

from pathlib import Path
from typing import Union

import duckdb


def initialize_database(db_path: Union[str, Path]) -> duckdb.DuckDBPyConnection:
    """Initialize database with schema.

    Args:
        db_path: Path to DuckDB database file

    Returns:
        DuckDB connection

    Note:
        This function is idempotent - can be called multiple times safely.
    """
    conn = duckdb.connect(str(db_path))

    # Create lyrics_corpus table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lyrics_corpus (
            corpus_id VARCHAR PRIMARY KEY,
            title VARCHAR,
            artist VARCHAR,
            content_hash VARCHAR NOT NULL UNIQUE,
            created_at TIMESTAMP NOT NULL
        )
    """)

    # Create lyric_tokens table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lyric_tokens (
            token_id VARCHAR PRIMARY KEY,
            lyrics_corpus_id VARCHAR NOT NULL,
            surface VARCHAR NOT NULL,
            reading VARCHAR NOT NULL,
            lemma VARCHAR NOT NULL,
            pos VARCHAR NOT NULL,
            line_index INTEGER NOT NULL,
            token_index INTEGER NOT NULL,
            moras_json VARCHAR NOT NULL,
            FOREIGN KEY (lyrics_corpus_id) REFERENCES lyrics_corpus(corpus_id)
        )
    """)

    # Create match_runs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS match_runs (
            run_id VARCHAR PRIMARY KEY,
            lyrics_corpus_id VARCHAR NOT NULL,
            input_text VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            config_json VARCHAR NOT NULL,
            FOREIGN KEY (lyrics_corpus_id) REFERENCES lyrics_corpus(corpus_id)
        )
    """)

    # Create match_results table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            result_id VARCHAR PRIMARY KEY,
            run_id VARCHAR NOT NULL,
            token_id VARCHAR,
            input_token VARCHAR NOT NULL,
            input_reading VARCHAR NOT NULL,
            match_type VARCHAR NOT NULL,
            matched_token_ids_json VARCHAR,
            mora_details_json VARCHAR,
            FOREIGN KEY (run_id) REFERENCES match_runs(run_id),
            FOREIGN KEY (token_id) REFERENCES lyric_tokens(token_id)
        )
    """)

    # Create indexes for performance
    # Index on lyrics_corpus.content_hash (already UNIQUE)

    # Indexes on lyric_tokens
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_lyric_tokens_corpus_surface
        ON lyric_tokens(lyrics_corpus_id, surface)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_lyric_tokens_corpus_reading
        ON lyric_tokens(lyrics_corpus_id, reading)
    """)

    # Index on match_results
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_match_results_run_id
        ON match_results(run_id)
    """)

    return conn
