"""Tests for application settings."""

from pathlib import Path


def test_settings_default_values():
    """Test that settings have correct default values."""
    from src.infrastructure.config.settings import Settings

    settings = Settings()

    # Check defaults
    assert settings.db_path == "lyric_talk.duckdb"
    assert settings.nlp_model == "ja_ginza"
    assert settings.max_mora_length == 5
    assert settings.output_format == "json"
    assert settings.log_level == "INFO"


def test_settings_from_env_variables(monkeypatch):
    """Test that settings can be loaded from environment variables."""
    from src.infrastructure.config.settings import Settings

    # Set environment variables
    monkeypatch.setenv("LYRIC_TALK_DB_PATH", "/custom/path/db.duckdb")
    monkeypatch.setenv("LYRIC_TALK_NLP_MODEL", "custom_model")
    monkeypatch.setenv("LYRIC_TALK_MAX_MORA_LENGTH", "10")

    # Create new settings instance
    settings = Settings()

    # Verify values from environment
    assert settings.db_path == "/custom/path/db.duckdb"
    assert settings.nlp_model == "custom_model"
    assert settings.max_mora_length == 10


def test_settings_db_path_resolved():
    """Test that db_path_resolved returns a Path object."""
    from src.infrastructure.config.settings import Settings

    settings = Settings(db_path="test.duckdb")

    # Should return a resolved Path
    resolved = settings.db_path_resolved
    assert isinstance(resolved, Path)
    assert resolved.name == "test.duckdb"


def test_settings_case_insensitive(monkeypatch):
    """Test that environment variable names are case insensitive."""
    from src.infrastructure.config.settings import Settings

    # Set with different case
    monkeypatch.setenv("lyric_talk_db_path", "lowercase.db")
    monkeypatch.setenv("LYRIC_TALK_NLP_MODEL", "UPPERCASE")

    settings = Settings()

    # Should work with any case
    assert settings.db_path == "lowercase.db"
    assert settings.nlp_model == "UPPERCASE"


def test_global_settings_instance():
    """Test that global settings instance is available."""
    from src.infrastructure.config.settings import settings

    # Should be a Settings instance
    assert hasattr(settings, "db_path")
    assert hasattr(settings, "nlp_model")
    assert hasattr(settings, "max_mora_length")
