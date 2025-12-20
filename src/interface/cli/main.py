"""CLI main entry point for lyric-talk."""

import argparse
import sys
from pathlib import Path
from typing import NoReturn, Optional

import duckdb

from src.application.use_cases.match_text import MatchTextUseCase
from src.application.use_cases.query_results import QueryResultsUseCase
from src.application.use_cases.register_lyrics import RegisterLyricsUseCase
from src.infrastructure.config.settings import Settings
from src.infrastructure.database.duckdb_lyric_token_repository import (
    DuckDBLyricTokenRepository,
)
from src.infrastructure.database.duckdb_lyrics_repository import DuckDBLyricsRepository
from src.infrastructure.database.duckdb_match_repository import DuckDBMatchRepository
from src.infrastructure.database.schema import initialize_database
from src.infrastructure.nlp.spacy_nlp_service import SpacyNlpService


def read_text_input(file_path: Optional[str], text: Optional[str]) -> str:
    """Read text from file or direct input.

    Args:
        file_path: Path to text file (optional)
        text: Direct text input (optional)

    Returns:
        Text content

    Raises:
        SystemExit: If neither file_path nor text is provided
    """
    if file_path is not None and file_path != "":
        try:
            with Path(file_path).open(mode="r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif text is not None:
        return text
    else:
        print("Error: Either file path or --text must be provided", file=sys.stderr)
        sys.exit(2)


def create_db_connection(settings: Settings) -> duckdb.DuckDBPyConnection:
    """Create database connection and initialize schema.

    Args:
        settings: Application settings

    Returns:
        Database connection
    """
    return initialize_database(settings.db_path_resolved)


def create_register_use_case(
    settings: Optional[Settings] = None,
) -> RegisterLyricsUseCase:
    """Create RegisterLyricsUseCase with dependencies.

    Args:
        settings: Application settings (uses default if None)

    Returns:
        RegisterLyricsUseCase instance
    """
    if settings is None:
        settings = Settings()

    # Initialize database schema
    nlp_service = SpacyNlpService(model_name=settings.nlp_model)
    lyrics_repo = DuckDBLyricsRepository(str(settings.db_path_resolved))
    lyric_token_repo = DuckDBLyricTokenRepository(str(settings.db_path_resolved))

    return RegisterLyricsUseCase(
        nlp_service=nlp_service,
        lyrics_repository=lyrics_repo,
        lyric_token_repository=lyric_token_repo,
    )


def create_match_use_case(settings: Optional[Settings] = None) -> MatchTextUseCase:
    """Create MatchTextUseCase with dependencies.

    Args:
        settings: Application settings (uses default if None)

    Returns:
        MatchTextUseCase instance
    """
    if settings is None:
        settings = Settings()

    # Initialize database schema
    conn = create_db_connection(settings)
    conn.close()

    nlp_service = SpacyNlpService(model_name=settings.nlp_model)
    lyric_token_repo = DuckDBLyricTokenRepository(str(settings.db_path_resolved))
    match_repo = DuckDBMatchRepository(str(settings.db_path_resolved))

    return MatchTextUseCase(
        nlp_service=nlp_service,
        lyric_token_repository=lyric_token_repo,
        match_repository=match_repo,
        max_mora_length=settings.max_mora_length,
    )


def create_query_use_case(settings: Optional[Settings] = None) -> QueryResultsUseCase:
    """Create QueryResultsUseCase with dependencies.

    Args:
        settings: Application settings (uses default if None)

    Returns:
        QueryResultsUseCase instance
    """
    if settings is None:
        settings = Settings()

    # Initialize database schema
    conn = create_db_connection(settings)
    conn.close()

    match_repo = DuckDBMatchRepository(str(settings.db_path_resolved))
    lyric_token_repo = DuckDBLyricTokenRepository(str(settings.db_path_resolved))

    return QueryResultsUseCase(
        match_repository=match_repo,
        lyric_token_repository=lyric_token_repo,
    )


def handle_register(args: argparse.Namespace) -> None:
    """Handle register subcommand.

    Args:
        args: Parsed command-line arguments
    """
    lyrics_text = read_text_input(args.file, args.text)
    use_case = create_register_use_case()

    try:
        corpus_id = use_case.execute(lyrics_text)
        print(f"Successfully registered lyrics with corpus_id: {corpus_id}")
    except Exception as e:
        print(f"Error registering lyrics: {e}", file=sys.stderr)
        sys.exit(1)


def handle_match(args: argparse.Namespace) -> None:
    """Handle match subcommand.

    Args:
        args: Parsed command-line arguments
    """
    input_text = read_text_input(args.file, args.text)
    corpus_id = args.corpus_id
    use_case = create_match_use_case()

    try:
        run_id = use_case.execute(input_text, corpus_id)
        print(f"Successfully matched text with run_id: {run_id}")
    except Exception as e:
        print(f"Error matching text: {e}", file=sys.stderr)
        sys.exit(1)


def handle_query(args: argparse.Namespace) -> None:
    """Handle query subcommand.

    Args:
        args: Parsed command-line arguments
    """
    use_case = create_query_use_case()

    try:
        results = use_case.execute(args.run_id)

        if results is None:
            print(f"Error: Match run not found: {args.run_id}", file=sys.stderr)
            sys.exit(1)

        # Display results
        match_run = results["match_run"]
        print(f"Match Run ID: {match_run.run_id}")
        print(f"Input Text: {match_run.input_text}")
        print(f"Timestamp: {match_run.timestamp}")
        print(f"\nResults: {len(results['results'])} matches")

        for idx, result_data in enumerate(results["results"], 1):
            match_result = result_data["match_result"]
            resolved_tokens = result_data["resolved_tokens"]

            print(f"\n--- Match {idx} ---")
            print(f"Match Type: {match_result.match_type}")
            print(f"Matched Tokens: {len(resolved_tokens)}")
            for token in resolved_tokens:
                print(
                    f"  - {token.surface} (reading: {token.reading.normalized}, "
                    f"lemma: {token.lemma}, pos: {token.pos})"
                )

    except Exception as e:
        print(f"Error querying results: {e}", file=sys.stderr)
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="lyric-talk",
        description="Lyric matching tool using DDD + Onion Architecture",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register subcommand
    register_parser = subparsers.add_parser("register", help="Register lyrics into the database")
    register_input_group = register_parser.add_mutually_exclusive_group(required=True)
    register_input_group.add_argument("file", nargs="?", help="Path to lyrics text file")
    register_input_group.add_argument("--text", "-t", help="Lyrics text as string")

    # Match subcommand
    match_parser = subparsers.add_parser("match", help="Match text against lyrics")
    match_parser.add_argument("corpus_id", help="Lyrics corpus ID to match against")
    match_input_group = match_parser.add_mutually_exclusive_group(required=True)
    match_input_group.add_argument("file", nargs="?", help="Path to input text file")
    match_input_group.add_argument("--text", "-t", help="Input text as string")

    # Query subcommand
    query_parser = subparsers.add_parser("query", help="Query match results")
    query_parser.add_argument("run_id", help="Match run ID to query")

    return parser


def main() -> NoReturn:
    """Main entry point for CLI.

    Raises:
        SystemExit: Always (normal exit or error)
    """
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(2)

    try:
        if args.command == "register":
            handle_register(args)
        elif args.command == "match":
            handle_match(args)
        elif args.command == "query":
            handle_query(args)
        else:
            parser.print_help()
            sys.exit(2)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)

    sys.exit(0)


if __name__ == "__main__":
    main()
