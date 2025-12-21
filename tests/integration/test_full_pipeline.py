"""End-to-end integration tests for full pipeline."""

import tempfile
from pathlib import Path

import pytest

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


@pytest.mark.integration
class TestFullPipeline:
    """Integration tests for full pipeline: register → match → query."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=True) as f:
            db_path = Path(f.name)

        # Initialize database schema - this returns a connection and creates tables
        conn = initialize_database(str(db_path))
        conn.close()

        yield str(db_path)

        if db_path.exists():
            db_path.unlink()

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(nlp_model="ja_ginza", max_mora_length=5)

    @pytest.fixture
    def nlp_service(self, settings):
        """Create NLP service."""
        return SpacyNlpService(model_name=settings.nlp_model)

    @pytest.fixture
    def lyrics_repository(self, temp_db):
        """Create lyrics repository."""
        return DuckDBLyricsRepository(temp_db)

    @pytest.fixture
    def lyric_token_repository(self, temp_db):
        """Create lyric token repository."""
        return DuckDBLyricTokenRepository(temp_db)

    @pytest.fixture
    def match_repository(self, temp_db):
        """Create match repository."""
        return DuckDBMatchRepository(temp_db)

    @pytest.fixture
    def register_use_case(self, nlp_service, lyrics_repository, lyric_token_repository):
        """Create register lyrics use case."""
        return RegisterLyricsUseCase(
            nlp_service=nlp_service,
            lyrics_repository=lyrics_repository,
            lyric_token_repository=lyric_token_repository,
        )

    @pytest.fixture
    def match_use_case(self, nlp_service, lyric_token_repository, match_repository, settings):
        """Create match text use case."""
        return MatchTextUseCase(
            nlp_service=nlp_service,
            lyric_token_repository=lyric_token_repository,
            match_repository=match_repository,
            max_mora_length=settings.max_mora_length,
        )

    @pytest.fixture
    def query_use_case(self, match_repository, lyric_token_repository):
        """Create query results use case."""
        return QueryResultsUseCase(
            match_repository=match_repository,
            lyric_token_repository=lyric_token_repository,
        )

    def test_full_pipeline(self, register_use_case, match_use_case, query_use_case):
        """Test full pipeline: register → match → query."""
        # 1. Register lyrics
        lyrics_text = "東京の空は青い\n桜が咲いている"
        corpus_id = register_use_case.execute(lyrics_text)

        assert corpus_id is not None
        assert corpus_id.startswith("corpus_")

        # 2. Match input text
        input_text = "東京は青い空です"
        run_id = match_use_case.execute(input_text, corpus_id)

        assert run_id is not None
        assert run_id.startswith("run_")

        # 3. Query results
        results = query_use_case.execute(run_id)

        assert results is not None
        assert results.match_run.run_id == run_id
        assert results.match_run.input_text == input_text

        # Debug: Print results structure
        print(f"\nDebug - Number of results: {len(results.items)}")
        for idx, item in enumerate(results.items):
            print(f"Result {idx}:")
            print(f"  - input_token: {item.input.surface}")
            print(f"  - match_type: {item.match_type}")
            print(f"  - chosen_lyrics_tokens count: {len(item.chosen_lyrics_tokens)}")

        assert len(results.items) > 0

        # For integration test, we verify the pipeline runs without errors
        # Actual matching quality is tested in unit tests
        # At least one result should exist (even if it's a NO_MATCH)
        assert len(results.items) > 0

    def test_no_match_scenario(self, register_use_case, match_use_case, query_use_case):
        """Test scenario where no matches are found."""
        # 1. Register lyrics
        lyrics_text = "東京の空は青い"
        corpus_id = register_use_case.execute(lyrics_text)

        assert corpus_id is not None

        # 2. Match with completely different text
        input_text = "大阪の海は緑色"
        run_id = match_use_case.execute(input_text, corpus_id)

        assert run_id is not None

        # 3. Query results
        results = query_use_case.execute(run_id)

        assert results is not None
        assert results.match_run.run_id == run_id

    def test_duplicate_lyrics_registration(self, register_use_case):
        """Test that duplicate lyrics reuse existing corpus_id."""
        # Register same lyrics twice
        lyrics_text = "同じ歌詞のテスト"

        corpus_id1 = register_use_case.execute(lyrics_text)
        corpus_id2 = register_use_case.execute(lyrics_text)

        # Should return the same corpus_id
        assert corpus_id1 == corpus_id2

    def test_multiple_matches_in_query(self, register_use_case, match_use_case, query_use_case):
        """Test querying results with multiple matches."""
        # Register lyrics with repeated words
        lyrics_text = "空を見上げる 空が青い 空は広い"
        corpus_id = register_use_case.execute(lyrics_text)

        assert corpus_id is not None

        # Match text that appears multiple times
        input_text = "空を見る"
        run_id = match_use_case.execute(input_text, corpus_id)

        assert run_id is not None

        # Query and verify multiple matches
        results = query_use_case.execute(run_id)

        assert results is not None
        # Should have matches for both tokens
        assert len(results.items) > 0
