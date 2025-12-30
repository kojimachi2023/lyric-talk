"""Tests for CLI main."""

from unittest import mock

import pytest
from typer.testing import CliRunner

from src.interface.cli.main import app, read_text_input


class TestCliMain:
    """Test suite for CLI main."""

    @pytest.fixture
    def runner(self):
        """Create a CliRunner for testing."""
        return CliRunner()

    def test_read_text_input_allows_empty_text(self):
        """Test read_text_input accepts empty string for --text."""
        assert read_text_input(file_path=None, text="") == ""

    def test_read_text_input_file_not_found(self, runner):
        """Test read_text_input with non-existent file."""
        with pytest.raises(SystemExit) as exc_info:
            read_text_input(file_path="/nonexistent/file.txt", text=None)

        assert exc_info.value.code == 1

    def test_read_text_input_file_read_error(self, runner):
        """Test read_text_input with file read error."""
        with mock.patch("pathlib.Path.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(SystemExit) as exc_info:
                read_text_input(file_path="/some/file.txt", text=None)

            assert exc_info.value.code == 1

    def test_read_text_input_no_input_provided(self, runner):
        """Test read_text_input without file or text."""
        with pytest.raises(SystemExit) as exc_info:
            read_text_input(file_path=None, text=None)

        assert exc_info.value.code == 2

    def test_register_command_with_file(self, runner):
        """Test register command with text file."""
        test_lyrics = "テストの歌詞です\n二行目の歌詞"

        mock_uow = mock.MagicMock()
        mock_nlp = mock.Mock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.return_value = "corpus_123"

        mock_file = mock.mock_open(read_data=test_lyrics)
        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(
                db_path_resolved="test.duckdb", nlp_model="ja_ginza"
            )
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch("src.interface.cli.main.SpacyNlpService", return_value=mock_nlp):
                    with mock.patch(
                        "src.interface.cli.main.RegisterLyricsUseCase",
                        return_value=mock_use_case,
                    ):
                        with mock.patch("pathlib.Path.open", mock_file):
                            result = runner.invoke(app, ["register", "test.txt"])

        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once_with(test_lyrics)
        assert "corpus_123" in result.stdout

    def test_register_command_with_text(self, runner):
        """Test register command with direct text."""
        test_lyrics = "直接入力の歌詞"

        mock_uow = mock.MagicMock()
        mock_nlp = mock.Mock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.return_value = "corpus_456"

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(
                db_path_resolved="test.duckdb", nlp_model="ja_ginza"
            )
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch("src.interface.cli.main.SpacyNlpService", return_value=mock_nlp):
                    with mock.patch(
                        "src.interface.cli.main.RegisterLyricsUseCase",
                        return_value=mock_use_case,
                    ):
                        result = runner.invoke(app, ["register", "--text", test_lyrics])

        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once_with(test_lyrics)
        assert "corpus_456" in result.stdout

    def test_match_command_with_file(self, runner):
        """Test match command with text file."""
        test_text = "マッチするテキスト"
        corpus_id = "corpus_123"

        mock_uow = mock.MagicMock()
        mock_nlp = mock.Mock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.return_value = "run_789"

        mock_file = mock.mock_open(read_data=test_text)
        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(
                db_path_resolved="test.duckdb",
                nlp_model="ja_ginza",
                max_mora_length=5,
            )
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch("src.interface.cli.main.SpacyNlpService", return_value=mock_nlp):
                    with mock.patch(
                        "src.interface.cli.main.MatchTextUseCase",
                        return_value=mock_use_case,
                    ):
                        with mock.patch("pathlib.Path.open", mock_file):
                            result = runner.invoke(app, ["match", corpus_id, "test.txt"])

        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once_with(test_text, corpus_id)
        assert "run_789" in result.stdout

    def test_match_command_with_text(self, runner):
        """Test match command with direct text."""
        test_text = "直接入力のマッチテキスト"
        corpus_id = "corpus_456"

        mock_uow = mock.MagicMock()
        mock_nlp = mock.Mock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.return_value = "run_abc"

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(
                db_path_resolved="test.duckdb",
                nlp_model="ja_ginza",
                max_mora_length=5,
            )
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch("src.interface.cli.main.SpacyNlpService", return_value=mock_nlp):
                    with mock.patch(
                        "src.interface.cli.main.MatchTextUseCase",
                        return_value=mock_use_case,
                    ):
                        result = runner.invoke(app, ["match", corpus_id, "--text", test_text])

        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once_with(test_text, corpus_id)
        assert "run_abc" in result.stdout

    def test_query_command(self, runner):
        """Test query command."""
        from datetime import datetime

        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()
        mock_result = mock.Mock(
            match_run=mock.Mock(
                run_id="run_123",
                input_text="test input",
                timestamp=datetime(2025, 1, 1),
            ),
            items=[],
            summary=mock.Mock(
                reconstructed_surface="",
                reconstructed_reading="",
                stats=mock.Mock(
                    exact_surface_count=0,
                    exact_reading_count=0,
                    mora_combination_count=0,
                ),
            ),
        )
        mock_use_case.execute.return_value = mock_result

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.QueryResultsUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["query", "run_123"])

        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once_with("run_123")
        assert "run_123" in result.stdout

    def test_query_command_not_found(self, runner):
        """Test query command when run_id is not found."""
        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.return_value = None

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.QueryResultsUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["query", "run_notfound"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "not found" in result.stdout.lower()

    def test_missing_subcommand(self, runner):
        """Test CLI without subcommand shows help."""
        result = runner.invoke(app, [])
        assert result.exit_code in [0, 2]
        assert "Usage:" in result.stdout or "Commands:" in result.stdout or result.exit_code == 2

    def test_register_missing_input(self, runner):
        """Test register command without file or text."""
        result = runner.invoke(app, ["register"])
        assert result.exit_code == 2

    def test_match_missing_input(self, runner):
        """Test match command without file or text."""
        result = runner.invoke(app, ["match", "corpus_123"])
        assert result.exit_code == 2

    def test_corpus_list_command(self, runner):
        """Test corpus list command."""
        from datetime import datetime

        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()
        mock_summary = mock.Mock(
            lyrics_corpus_id="corpus_123",
            title="Test Song",
            artist="Test Artist",
            token_count=42,
            preview_text="テストの歌詞プレビュー",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        mock_use_case.execute.return_value = [mock_summary]

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListLyricsCorporaUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["corpus", "list"])

        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once()
        assert "corpus_123" in result.stdout
        assert "Lyrics Corpora" in result.stdout

    def test_corpus_list_empty(self, runner):
        """Test corpus list when no corpora exist."""
        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.return_value = []

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListLyricsCorporaUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["corpus", "list"])

        assert result.exit_code == 0
        assert "No lyrics corpora found" in result.stdout or "found" in result.stdout.lower()

    def test_run_list_command(self, runner):
        """Test run list command."""
        from datetime import datetime

        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()
        mock_summary = mock.Mock(
            run_id="run_789",
            lyrics_corpus_id="corpus_123",
            input_text="テストの入力テキスト",
            results_count=5,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )
        mock_use_case.execute.return_value = [mock_summary]

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListMatchRunsUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["run", "list"])

        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once()
        assert "run_789" in result.stdout
        assert "corpus_123" in result.stdout

    def test_run_list_empty(self, runner):
        """Test run list when no runs exist."""
        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.return_value = []

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListMatchRunsUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["run", "list"])

        assert result.exit_code == 0
        assert "No match runs found" in result.stdout or "found" in result.stdout.lower()

    def test_match_with_corpus_id_selection_non_tty(self, runner):
        """Test match command with corpus_id omitted in non-TTY mode."""
        test_text = "マッチするテキスト"

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(
                db_path_resolved="test.duckdb",
                nlp_model="ja_ginza",
                max_mora_length=5,
            )
            with mock.patch("sys.stdin.isatty", return_value=False):
                result = runner.invoke(app, ["match", "--text", test_text])

        assert result.exit_code == 1
        output_all = result.stdout + result.output
        assert "required" in output_all.lower() or "non-interactive" in output_all.lower()

    def test_match_with_auto_select_single_corpus(self, runner):
        """Test match command auto-selects when only one corpus exists."""
        mock_uow = mock.MagicMock()
        mock_nlp = mock.Mock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.return_value = "run_explicit"

        test_text = "テスト"

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(
                db_path_resolved="test.duckdb",
                nlp_model="ja_ginza",
                max_mora_length=5,
            )
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch("src.interface.cli.main.SpacyNlpService", return_value=mock_nlp):
                    with mock.patch(
                        "src.interface.cli.main.MatchTextUseCase",
                        return_value=mock_use_case,
                    ):
                        result = runner.invoke(app, ["match", "corpus_123", "--text", test_text])

        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once_with(test_text, "corpus_123")

    def test_match_with_no_corpora(self, runner):
        """Test match command when no corpora exist."""
        mock_uow = mock.MagicMock()
        mock_list_use_case = mock.Mock()
        mock_list_use_case.execute.return_value = []

        test_text = "テスト"

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(
                db_path_resolved="test.duckdb",
                nlp_model="ja_ginza",
                max_mora_length=5,
            )
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListLyricsCorporaUseCase",
                    return_value=mock_list_use_case,
                ):
                    with mock.patch("sys.stdin.isatty", return_value=True):
                        with mock.patch("sys.stdout.isatty", return_value=True):
                            result = runner.invoke(app, ["match", "--text", test_text])

        assert result.exit_code == 1
        output_all = result.stdout + result.output
        assert "register" in output_all.lower() or "no" in output_all.lower()

    def test_query_with_explicit_run_id(self, runner):
        """Test query command with explicit run_id."""
        from datetime import datetime

        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()
        mock_result = mock.Mock(
            match_run=mock.Mock(
                run_id="run_explicit",
                input_text="test input",
                timestamp=datetime(2025, 1, 1),
            ),
            items=[],
            summary=mock.Mock(
                reconstructed_surface="",
                reconstructed_reading="",
                stats=mock.Mock(
                    exact_surface_count=0,
                    exact_reading_count=0,
                    mora_combination_count=0,
                ),
            ),
        )
        mock_use_case.execute.return_value = mock_result

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.QueryResultsUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["query", "run_explicit"])

        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once_with("run_explicit")
        assert "run_explicit" in result.stdout or "run_explicit" in result.output

    def test_query_with_no_runs_non_tty(self, runner):
        """Test query command without run_id in non-TTY mode."""
        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("sys.stdin.isatty", return_value=False):
                result = runner.invoke(app, ["query"])

        assert result.exit_code == 1
        output_all = result.stdout + result.output
        assert "required" in output_all.lower() or "non-interactive" in output_all.lower()

    def test_query_with_no_runs_available(self, runner):
        """Test query command when no runs exist."""
        mock_uow = mock.MagicMock()
        mock_list_use_case = mock.Mock()
        mock_list_use_case.execute.return_value = []

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListMatchRunsUseCase",
                    return_value=mock_list_use_case,
                ):
                    with mock.patch("sys.stdin.isatty", return_value=True):
                        with mock.patch("sys.stdout.isatty", return_value=True):
                            result = runner.invoke(app, ["query"])

        assert result.exit_code == 1
        output_all = result.stdout + result.output
        assert "match" in output_all.lower() or "no" in output_all.lower()

    def test_corpus_list_with_exception(self, runner):
        """Test corpus list command with exception."""
        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.side_effect = Exception("Database error")

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListLyricsCorporaUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["corpus", "list"], catch_exceptions=False)

        assert result.exit_code == 1

    def test_run_list_with_exception(self, runner):
        """Test run list command with exception."""
        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()
        mock_use_case.execute.side_effect = Exception("Database error")

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListMatchRunsUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["run", "list"], catch_exceptions=False)

        assert result.exit_code == 1

    def test_query_with_results_display(self, runner):
        """Test query command displays results with tree structure."""
        from datetime import datetime

        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()

        mock_input_token = mock.Mock(surface="東京", reading="トウキョウ")
        mock_lyric_token = mock.Mock(
            surface="東京",
            reading="トウキョウ",
            lemma="東京",
            pos="NOUN",
        )
        mock_item = mock.Mock(
            input=mock_input_token,
            match_type="exact_surface",
            chosen_lyrics_tokens=[mock_lyric_token],
            mora_trace=None,
        )

        mock_summary = mock.Mock(
            reconstructed_surface="東京",
            reconstructed_reading="トウキョウ",
            stats=mock.Mock(
                exact_surface_count=1,
                exact_reading_count=0,
                mora_combination_count=0,
            ),
        )

        mock_result = mock.Mock(
            match_run=mock.Mock(
                run_id="run_123",
                input_text="東京",
                timestamp=datetime(2025, 1, 1),
            ),
            items=[mock_item],
            summary=mock_summary,
        )
        mock_use_case.execute.return_value = mock_result

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.QueryResultsUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["query", "run_123"])

        assert result.exit_code == 0
        assert "run_123" in result.stdout or "東京" in result.stdout

    def test_query_with_mora_combination_results(self, runner):
        """Test query command displays mora combination results."""
        from datetime import datetime

        mock_uow = mock.MagicMock()
        mock_use_case = mock.Mock()

        mock_input_token = mock.Mock(surface="テスト", reading="テスト")
        mock_lyric_token = mock.Mock(
            surface="テ",
            reading="テ",
            lemma="テ",
            pos="NOUN",
        )
        mock_mora_item = mock.Mock(
            mora="テ",
            source_surface="テスト",
        )
        mock_mora_trace = mock.Mock(items=[mock_mora_item])
        mock_item = mock.Mock(
            input=mock_input_token,
            match_type="mora_combination",
            chosen_lyrics_tokens=[mock_lyric_token],
            mora_trace=mock_mora_trace,
        )

        mock_summary = mock.Mock(
            reconstructed_surface="テ",
            reconstructed_reading="テ",
            stats=mock.Mock(
                exact_surface_count=0,
                exact_reading_count=0,
                mora_combination_count=1,
            ),
        )

        mock_result = mock.Mock(
            match_run=mock.Mock(
                run_id="run_456",
                input_text="テスト",
                timestamp=datetime(2025, 1, 1),
            ),
            items=[mock_item],
            summary=mock_summary,
        )
        mock_use_case.execute.return_value = mock_result

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.QueryResultsUseCase",
                    return_value=mock_use_case,
                ):
                    result = runner.invoke(app, ["query", "run_456"])
                    assert result.exit_code == 0
                    mock_use_case.execute.assert_called_once_with("run_456")

    def test_main_keyboard_interrupt(self):
        """Test main function handles KeyboardInterrupt."""
        from src.interface.cli.main import main

        with mock.patch("src.interface.cli.main.app") as mock_app:
            mock_app.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 130

    def test_main_system_exit(self):
        """Test main function re-raises SystemExit."""
        from src.interface.cli.main import main

        with mock.patch("src.interface.cli.main.app") as mock_app:
            mock_app.side_effect = SystemExit(42)

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 42

    def test_match_list_corpora_exception(self, runner):
        """Test match command handles exception when listing corpora."""
        mock_uow = mock.MagicMock()
        mock_list_use_case = mock.Mock()
        mock_list_use_case.execute.side_effect = Exception("Database error")

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(
                db_path_resolved="test.duckdb",
                nlp_model="ja_ginza",
                max_mora_length=5,
            )
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListLyricsCorporaUseCase",
                    return_value=mock_list_use_case,
                ):
                    with mock.patch("sys.stdin.isatty", return_value=True):
                        with mock.patch("sys.stdout.isatty", return_value=True):
                            result = runner.invoke(app, ["match", "--text", "test"])

        assert result.exit_code == 1

    def test_query_list_runs_exception(self, runner):
        """Test query command handles exception when listing runs."""
        mock_uow = mock.MagicMock()
        mock_list_use_case = mock.Mock()
        mock_list_use_case.execute.side_effect = Exception("Database error")

        with mock.patch("src.interface.cli.main.get_settings_and_init_db") as mock_settings:
            mock_settings.return_value = mock.Mock(db_path_resolved="test.duckdb")
            with mock.patch("src.interface.cli.main.DuckDBUnitOfWork") as mock_uow_class:
                mock_uow_class.return_value.__enter__ = mock.Mock(return_value=mock_uow)
                mock_uow_class.return_value.__exit__ = mock.Mock(return_value=False)
                with mock.patch(
                    "src.interface.cli.main.ListMatchRunsUseCase",
                    return_value=mock_list_use_case,
                ):
                    with mock.patch("sys.stdin.isatty", return_value=True):
                        with mock.patch("sys.stdout.isatty", return_value=True):
                            result = runner.invoke(app, ["query"])

        assert result.exit_code == 1
