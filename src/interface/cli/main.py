"""CLI main entry point for lyric-talk."""

import sys
from pathlib import Path
from typing import NoReturn, Optional

import duckdb
import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from src.application.use_cases.list_lyrics_corpora import ListLyricsCorporaUseCase
from src.application.use_cases.list_match_runs import ListMatchRunsUseCase
from src.application.use_cases.match_text import MatchTextUseCase
from src.application.use_cases.query_results import QueryResultsUseCase
from src.application.use_cases.register_lyrics import RegisterLyricsUseCase
from src.infrastructure.config.settings import Settings
from src.infrastructure.database.duckdb_unit_of_work import DuckDBUnitOfWork
from src.infrastructure.database.schema import initialize_database
from src.infrastructure.nlp.spacy_nlp_service import SpacyNlpService

# Create Typer app
app = typer.Typer(
    name="lyric-talk",
    help="Lyric matching tool using DDD + Onion Architecture",
    add_completion=False,
)

# Create Rich console
console = Console()
console_err = Console(stderr=True)

# Create subcommand groups
corpus_app = typer.Typer(help="Manage lyrics corpora")
run_app = typer.Typer(help="Manage match runs")

app.add_typer(corpus_app, name="corpus")
app.add_typer(run_app, name="run")


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


def get_settings_and_init_db(settings: Optional[Settings] = None) -> Settings:
    """Get settings and initialize database schema.

    Args:
        settings: Application settings (uses default if None)

    Returns:
        Settings instance
    """
    if settings is None:
        settings = Settings()

    # Initialize database schema
    conn = create_db_connection(settings)
    conn.close()

    return settings


@corpus_app.command("list")
def corpus_list(
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of corpora to display"),
) -> None:
    """List all lyrics corpora."""
    settings = get_settings_and_init_db()

    try:
        with DuckDBUnitOfWork(str(settings.db_path_resolved)) as uow:
            use_case = ListLyricsCorporaUseCase(unit_of_work=uow)
            corpora = use_case.execute(limit=limit)

            if not corpora:
                console.print(
                    "[yellow]No lyrics corpora found. Register some lyrics first.[/yellow]"
                )
                return

            # Create Rich table
            table = Table(title=f"Lyrics Corpora (最新 {len(corpora)} 件)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Artist", style="green")
            table.add_column("Tokens", justify="right", style="blue")
            table.add_column("Preview", style="dim")
            table.add_column("Created", style="dim")

            for corpus in corpora:
                preview = (
                    corpus.preview_text[:50] + "..."
                    if len(corpus.preview_text) > 50
                    else corpus.preview_text
                )
                table.add_row(
                    corpus.lyrics_corpus_id,
                    corpus.title or "(no title)",
                    corpus.artist or "(unknown)",
                    str(corpus.token_count),
                    preview,
                    corpus.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                )

            console.print(table)

    except Exception as e:
        console_err.print(f"[red]Error listing corpora: {e}[/red]")
        raise typer.Exit(1)


@run_app.command("list")
def run_list(
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of runs to display"),
) -> None:
    """List all match runs."""
    settings = get_settings_and_init_db()

    try:
        with DuckDBUnitOfWork(str(settings.db_path_resolved)) as uow:
            use_case = ListMatchRunsUseCase(unit_of_work=uow)
            runs = use_case.execute(limit=limit)

            if not runs:
                console.print("[yellow]No match runs found. Run some matches first.[/yellow]")
                return

            # Create Rich table
            table = Table(title=f"Match Runs (最新 {len(runs)} 件)")
            table.add_column("Run ID", style="cyan", no_wrap=True)
            table.add_column("Corpus ID", style="magenta", no_wrap=True)
            table.add_column("Input Text", style="white")
            table.add_column("Results", justify="right", style="blue")
            table.add_column("Timestamp", style="dim")

            for run in runs:
                input_preview = (
                    run.input_text[:40] + "..." if len(run.input_text) > 40 else run.input_text
                )
                table.add_row(
                    run.run_id,
                    run.lyrics_corpus_id,
                    input_preview,
                    str(run.results_count),
                    run.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                )

            console.print(table)

    except Exception as e:
        console_err.print(f"[red]Error listing runs: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def register(
    file: Optional[str] = typer.Argument(None, help="Path to lyrics text file"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Lyrics text as string"),
) -> None:
    """Register lyrics into the database."""
    lyrics_text = read_text_input(file, text)
    settings = get_settings_and_init_db()

    try:
        with DuckDBUnitOfWork(str(settings.db_path_resolved)) as uow:
            nlp_service = SpacyNlpService(model_name=settings.nlp_model)
            use_case = RegisterLyricsUseCase(nlp_service=nlp_service, unit_of_work=uow)
            corpus_id = use_case.execute(lyrics_text)
            uow.commit()
        typer.echo(f"Successfully registered lyrics with corpus_id: {corpus_id}")
    except Exception as e:
        typer.echo(f"Error registering lyrics: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def match(
    corpus_id: Optional[str] = typer.Argument(
        None,
        help="Lyrics corpus ID to match against (optional, will prompt if omitted)",
    ),
    file: Optional[str] = typer.Argument(None, help="Path to input text file"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Input text as string"),
) -> None:
    """Match text against lyrics."""
    input_text = read_text_input(file, text)
    settings = get_settings_and_init_db()

    # If corpus_id is not provided, prompt for selection
    if corpus_id is None:
        # Check if we're in a TTY (interactive terminal)
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            console_err.print("[red]Error: --corpus-id is required in non-interactive mode.[/red]")
            console_err.print(
                "[yellow]Hint: Run 'corpus list' to see available corpora, "
                "then specify --corpus-id.[/yellow]"
            )
            raise typer.Exit(1)

        # Get list of corpora
        try:
            with DuckDBUnitOfWork(str(settings.db_path_resolved)) as uow:
                list_use_case = ListLyricsCorporaUseCase(unit_of_work=uow)
                corpora = list_use_case.execute(limit=50)

            if len(corpora) == 0:
                console.print(
                    "[yellow]No lyrics corpora found. Please register some lyrics first.[/yellow]"
                )
                raise typer.Exit(1)
            elif len(corpora) == 1:
                # Auto-select the only corpus
                corpus_id = corpora[0].lyrics_corpus_id
                console.print(
                    f"[green]Auto-selected corpus: {corpus_id} "
                    f"({corpora[0].title or 'no title'})[/green]"
                )
            else:
                # Prompt user to select
                console.print("[cyan]Available lyrics corpora:[/cyan]")
                for i, corpus in enumerate(corpora, 1):
                    console.print(
                        f"  {i}. {corpus.lyrics_corpus_id} - "
                        f"{corpus.title or '(no title)'} by {corpus.artist or '(unknown)'}"
                    )

                # Get user selection
                while True:
                    selection = typer.prompt(
                        f"Select corpus (1-{len(corpora)})", type=int, default=1
                    )
                    if 1 <= selection <= len(corpora):
                        corpus_id = corpora[selection - 1].lyrics_corpus_id
                        console.print(f"[green]Selected: {corpus_id}[/green]")
                        break
                    else:
                        console.print(
                            f"[red]Invalid selection. Please choose 1-{len(corpora)}[/red]"
                        )

        except Exception as e:
            console_err.print(f"[red]Error listing corpora: {e}[/red]")
            raise typer.Exit(1)

    # Execute match with selected or provided corpus_id
    try:
        with DuckDBUnitOfWork(str(settings.db_path_resolved)) as uow:
            nlp_service = SpacyNlpService(model_name=settings.nlp_model)
            use_case = MatchTextUseCase(
                nlp_service=nlp_service,
                unit_of_work=uow,
                max_mora_length=settings.max_mora_length,
            )
            run_id = use_case.execute(input_text, corpus_id)
            uow.commit()
        typer.echo(f"Successfully matched text with run_id: {run_id}")
    except Exception as e:
        typer.echo(f"Error matching text: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def query(
    run_id: Optional[str] = typer.Argument(
        None, help="Match run ID to query (optional, will prompt if omitted)"
    ),
) -> None:
    """Query match results with Rich Tree display."""
    settings = get_settings_and_init_db()

    # If run_id is not provided, prompt for selection
    if run_id is None:
        # Check if we're in a TTY (interactive terminal)
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            console_err.print("[red]Error: --run-id is required in non-interactive mode.[/red]")
            console_err.print(
                "[yellow]Hint: Run 'run list' to see available runs, then specify run_id.[/yellow]"
            )
            raise typer.Exit(1)

        # Get list of runs
        try:
            with DuckDBUnitOfWork(str(settings.db_path_resolved)) as uow:
                list_use_case = ListMatchRunsUseCase(unit_of_work=uow)
                runs = list_use_case.execute(limit=50)

            if len(runs) == 0:
                console.print(
                    "[yellow]No match runs found. Please run some matches first.[/yellow]"
                )
                raise typer.Exit(1)
            elif len(runs) == 1:
                # Auto-select the only run
                run_id = runs[0].run_id
                console.print(
                    f"[green]Auto-selected run: {run_id} ({runs[0].input_text[:30]}...)[/green]"
                )
            else:
                # Prompt user to select
                console.print("[cyan]Available match runs:[/cyan]")
                for i, run in enumerate(runs, 1):
                    input_preview = (
                        run.input_text[:40] + "..." if len(run.input_text) > 40 else run.input_text
                    )
                    console.print(
                        f"  {i}. {run.run_id} - {input_preview} ({run.results_count} matches)"
                    )

                # Get user selection
                while True:
                    selection = typer.prompt(f"Select run (1-{len(runs)})", type=int, default=1)
                    if 1 <= selection <= len(runs):
                        run_id = runs[selection - 1].run_id
                        console.print(f"[green]Selected: {run_id}[/green]")
                        break
                    else:
                        console.print(f"[red]Invalid selection. Please choose 1-{len(runs)}[/red]")

        except Exception as e:
            console_err.print(f"[red]Error listing runs: {e}[/red]")
            raise typer.Exit(1)

    # Execute query with selected or provided run_id
    try:
        with DuckDBUnitOfWork(str(settings.db_path_resolved)) as uow:
            use_case = QueryResultsUseCase(unit_of_work=uow)
            results = use_case.execute(run_id)

            if results is None:
                typer.echo(f"Error: Match run not found: {run_id}", err=True)
                raise typer.Exit(1)

            # Display results with Rich Tree
            match_run = results.match_run
            console.print(f"\n[bold cyan]Match Run: {match_run.run_id}[/bold cyan]")
            console.print(f"[dim]Input Text:[/dim] {match_run.input_text}")
            console.print(f"[dim]Timestamp:[/dim] {match_run.timestamp}")
            console.print(f"[dim]Matches Found:[/dim] {len(results.items)}\n")

            # Display summary if available
            if results.summary:
                console.print("[bold yellow]Summary:[/bold yellow]")
                console.print(f"  Reconstructed Surface: {results.summary.reconstructed_surface}")
                console.print(f"  Reconstructed Reading: {results.summary.reconstructed_reading}")
                console.print(
                    f"  Stats: exact_surface={results.summary.stats.exact_surface_count}, "
                    f"exact_reading={results.summary.stats.exact_reading_count}, "
                    f"mora_combination={results.summary.stats.mora_combination_count}\n"
                )

            if len(results.items) == 0:
                console.print("[yellow]No matches found in this run.[/yellow]")
            else:
                # Create Rich Tree for each match
                for idx, item in enumerate(results.items, 1):
                    # Create tree for this match
                    tree = Tree(
                        f"[bold green]Match {idx}: {item.match_type}[/bold green]",
                        guide_style="dim",
                    )

                    # Add input token info
                    input_branch = tree.add("[cyan]Input[/cyan]")
                    input_branch.add(f"{item.input.surface} [dim]({item.input.reading})[/dim]")

                    # Add matched lyrics tokens
                    tokens_branch = tree.add("[yellow]Matched Lyrics Tokens[/yellow]")
                    for token in item.chosen_lyrics_tokens:
                        tokens_branch.add(
                            f"{token.surface} [dim]([/dim]{token.reading}[dim])[/dim] "
                            f"[dim]│ lemma: {token.lemma} │ pos: {token.pos}[/dim]"
                        )

                    # Add mora trace details if available
                    if item.match_type == "mora_combination" and item.mora_trace:
                        details_branch = tree.add("[cyan]Mora Trace[/cyan]")
                        for trace_item in item.mora_trace.items:
                            details_branch.add(
                                f"Mora: {trace_item.mora} → "
                                f"Token: {trace_item.source_token_id} "
                                f"[dim](index: {trace_item.mora_index})[/dim]"
                            )

                    console.print(tree)
                    console.print()  # Add spacing between matches

    except Exception as e:
        typer.echo(f"Error querying results: {e}", err=True)
        raise typer.Exit(1)


def main() -> NoReturn:
    """Main entry point for CLI.

    Raises:
        SystemExit: Always (normal exit or error)
    """
    try:
        app()
    except SystemExit:
        # Typer already handles sys.exit, so re-raise
        raise
    except KeyboardInterrupt:
        typer.echo("\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception:
        # Let typer handle unexpected exceptions
        raise


if __name__ == "__main__":
    main()
