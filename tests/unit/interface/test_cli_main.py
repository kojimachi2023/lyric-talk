"""Tests for CLI main."""

from io import StringIO
from unittest import mock

import pytest


class TestCliMain:
    """Test suite for CLI main."""

    def test_read_text_input_allows_empty_text(self):
        """Test read_text_input accepts empty string for --text."""
        from src.interface.cli.main import read_text_input

        assert read_text_input(file_path=None, text="") == ""

    def test_create_match_use_case_wires_dependencies(self):
        """Test create_match_use_case wires dependencies without MatchingStrategy."""
        from src.infrastructure.config.settings import Settings
        from src.interface.cli.main import create_match_use_case

        settings = Settings(db_path="dummy.duckdb", nlp_model="ja_ginza", max_mora_length=7)

        mock_conn = mock.Mock()
        nlp_instance = mock.Mock()
        token_repo_instance = mock.Mock()
        match_repo_instance = mock.Mock()
        use_case_instance = mock.Mock()

        with mock.patch(
            "src.interface.cli.main.create_db_connection",
            return_value=mock_conn,
        ):
            with mock.patch(
                "src.interface.cli.main.SpacyNlpService",
                return_value=nlp_instance,
            ):
                with mock.patch(
                    "src.interface.cli.main.DuckDBLyricTokenRepository",
                    return_value=token_repo_instance,
                ):
                    with mock.patch(
                        "src.interface.cli.main.DuckDBMatchRepository",
                        return_value=match_repo_instance,
                    ):
                        with mock.patch(
                            "src.interface.cli.main.MatchTextUseCase",
                            return_value=use_case_instance,
                        ) as mock_use_case_cls:
                            created = create_match_use_case(settings)

        assert created is use_case_instance
        mock_conn.close.assert_called_once_with()
        mock_use_case_cls.assert_called_once_with(
            nlp_service=nlp_instance,
            lyric_token_repository=token_repo_instance,
            match_repository=match_repo_instance,
            max_mora_length=7,
        )

    def test_create_register_use_case_initializes_schema(self):
        """Test create_register_use_case initializes schema and wires dependencies."""
        from src.infrastructure.config.settings import Settings
        from src.interface.cli.main import create_register_use_case

        settings = Settings(db_path="dummy.duckdb", nlp_model="ja_ginza")

        mock_conn = mock.Mock()
        nlp_instance = mock.Mock()
        lyrics_repo_instance = mock.Mock()
        token_repo_instance = mock.Mock()
        use_case_instance = mock.Mock()

        with mock.patch(
            "src.interface.cli.main.create_db_connection",
            return_value=mock_conn,
        ):
            with mock.patch(
                "src.interface.cli.main.SpacyNlpService",
                return_value=nlp_instance,
            ):
                with mock.patch(
                    "src.interface.cli.main.DuckDBLyricsRepository",
                    return_value=lyrics_repo_instance,
                ):
                    with mock.patch(
                        "src.interface.cli.main.DuckDBLyricTokenRepository",
                        return_value=token_repo_instance,
                    ):
                        with mock.patch(
                            "src.interface.cli.main.RegisterLyricsUseCase",
                            return_value=use_case_instance,
                        ) as mock_use_case_cls:
                            created = create_register_use_case(settings)

        assert created is use_case_instance
        mock_conn.close.assert_called_once_with()
        mock_use_case_cls.assert_called_once_with(
            nlp_service=nlp_instance,
            lyrics_repository=lyrics_repo_instance,
            lyric_token_repository=token_repo_instance,
        )

    def test_register_command_with_file(self):
        """Test register command with text file."""
        from src.interface.cli.main import main

        # Mock RegisterLyricsUseCase
        mock_register_use_case = mock.Mock()
        mock_register_use_case.execute.return_value = "corpus_123"

        # Create test file
        test_lyrics = "テストの歌詞です\n二行目の歌詞"

        # Mock Path.open to return the test lyrics
        mock_file = mock.mock_open(read_data=test_lyrics)
        with mock.patch(
            "src.interface.cli.main.create_register_use_case",
            return_value=mock_register_use_case,
        ):
            with mock.patch("pathlib.Path.open", mock_file):
                with mock.patch("sys.argv", ["lyric-talk", "register", "test.txt"]):
                    with mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        with pytest.raises(SystemExit) as exc_info:
                            main()

        # Verify successful exit
        assert exc_info.value.code == 0

        # Verify use case was called with correct text
        mock_register_use_case.execute.assert_called_once_with(test_lyrics)

        # Verify output
        output = mock_stdout.getvalue()
        assert "corpus_123" in output

    def test_register_command_with_text(self):
        """Test register command with direct text."""
        from src.interface.cli.main import main

        # Mock RegisterLyricsUseCase
        mock_register_use_case = mock.Mock()
        mock_register_use_case.execute.return_value = "corpus_456"

        test_lyrics = "直接入力の歌詞"

        with mock.patch(
            "src.interface.cli.main.create_register_use_case",
            return_value=mock_register_use_case,
        ):
            with mock.patch("sys.argv", ["lyric-talk", "register", "--text", test_lyrics]):
                with mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        # Verify successful exit
        assert exc_info.value.code == 0

        # Verify use case was called
        mock_register_use_case.execute.assert_called_once_with(test_lyrics)

        # Verify output
        output = mock_stdout.getvalue()
        assert "corpus_456" in output

    def test_match_command_with_file(self):
        """Test match command with text file."""
        from src.interface.cli.main import main

        # Mock MatchTextUseCase
        mock_match_use_case = mock.Mock()
        mock_match_use_case.execute.return_value = "run_789"

        test_text = "マッチするテキスト"
        corpus_id = "corpus_123"

        # Mock Path.open to return the test text
        mock_file = mock.mock_open(read_data=test_text)
        with mock.patch(
            "src.interface.cli.main.create_match_use_case",
            return_value=mock_match_use_case,
        ):
            with mock.patch("pathlib.Path.open", mock_file):
                with mock.patch("sys.argv", ["lyric-talk", "match", corpus_id, "test.txt"]):
                    with mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        with pytest.raises(SystemExit) as exc_info:
                            main()

        # Verify successful exit
        assert exc_info.value.code == 0

        # Verify use case was called with corpus_id
        mock_match_use_case.execute.assert_called_once_with(test_text, corpus_id)

        # Verify output
        output = mock_stdout.getvalue()
        assert "run_789" in output

    def test_match_command_with_text(self):
        """Test match command with direct text."""
        from src.interface.cli.main import main

        # Mock MatchTextUseCase
        mock_match_use_case = mock.Mock()
        mock_match_use_case.execute.return_value = "run_abc"

        test_text = "直接入力のマッチテキスト"
        corpus_id = "corpus_456"

        with mock.patch(
            "src.interface.cli.main.create_match_use_case",
            return_value=mock_match_use_case,
        ):
            with mock.patch("sys.argv", ["lyric-talk", "match", corpus_id, "--text", test_text]):
                with mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        # Verify successful exit
        assert exc_info.value.code == 0

        # Verify use case was called with corpus_id
        mock_match_use_case.execute.assert_called_once_with(test_text, corpus_id)

        # Verify output
        output = mock_stdout.getvalue()
        assert "run_abc" in output

    def test_query_command(self):
        """Test query command."""
        from src.interface.cli.main import main

        # Mock QueryResultsUseCase
        mock_query_use_case = mock.Mock()
        mock_query_use_case.execute.return_value = {
            "match_run": mock.Mock(
                run_id="run_123",
                input_text="test input",
                timestamp=mock.Mock(__str__=lambda _: "2025-01-01 00:00:00"),
            ),
            "results": [],
        }

        with mock.patch(
            "src.interface.cli.main.create_query_use_case",
            return_value=mock_query_use_case,
        ):
            with mock.patch("sys.argv", ["lyric-talk", "query", "run_123"]):
                with mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        # Verify successful exit
        assert exc_info.value.code == 0

        # Verify use case was called
        mock_query_use_case.execute.assert_called_once_with("run_123")

        # Verify output
        output = mock_stdout.getvalue()
        assert "run_123" in output

    def test_query_command_not_found(self):
        """Test query command when run_id is not found."""
        from src.interface.cli.main import main

        # Mock QueryResultsUseCase returning None
        mock_query_use_case = mock.Mock()
        mock_query_use_case.execute.return_value = None

        with mock.patch(
            "src.interface.cli.main.create_query_use_case",
            return_value=mock_query_use_case,
        ):
            with mock.patch("sys.argv", ["lyric-talk", "query", "run_notfound"]):
                with mock.patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        # Verify exit code
        assert exc_info.value.code == 1

        # Verify error message
        error_output = mock_stderr.getvalue()
        assert "not found" in error_output.lower()

    def test_missing_subcommand(self):
        """Test CLI without subcommand shows help."""
        from src.interface.cli.main import main

        with mock.patch("sys.argv", ["lyric-talk"]):
            with mock.patch("sys.stderr", new_callable=StringIO):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        # Verify exit code (argparse returns 2 for invalid args)
        assert exc_info.value.code == 2

    def test_register_missing_input(self):
        """Test register command without file or text."""
        from src.interface.cli.main import main

        with mock.patch("sys.argv", ["lyric-talk", "register"]):
            with mock.patch("sys.stderr", new_callable=StringIO):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        # Verify exit code (argparse returns 2 for invalid args)
        assert exc_info.value.code == 2

    def test_match_missing_input(self):
        """Test match command without file or text."""
        from src.interface.cli.main import main

        with mock.patch("sys.argv", ["lyric-talk", "match", "corpus_123"]):
            with mock.patch("sys.stderr", new_callable=StringIO):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        # Verify exit code (argparse returns 2 for invalid args)
        assert exc_info.value.code == 2
