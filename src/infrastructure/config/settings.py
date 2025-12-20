"""Application settings using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Settings can be configured via environment variables with LYRIC_TALK_ prefix
    or via .env file.

    Example:
        LYRIC_TALK_DB_PATH=/path/to/db.duckdb
        LYRIC_TALK_NLP_MODEL=ja_ginza
    """

    # Database settings
    db_path: str = "lyric_talk.duckdb"

    # NLP settings
    nlp_model: str = "ja_ginza"

    # Matching settings
    max_mora_length: int = 5

    # Output settings
    output_format: str = "json"  # json, text, etc.

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="LYRIC_TALK_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def db_path_resolved(self) -> Path:
        """Get resolved database path."""
        return Path(self.db_path).resolve()


# Global settings instance
settings = Settings()
