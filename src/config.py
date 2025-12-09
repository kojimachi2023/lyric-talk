"""
設定クラス: pydantic-settingsを使用したアプリケーション設定
環境変数または.envファイルから設定値を読み込み可能
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(
        env_prefix="LYRIC_TALK_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # モーラ組み合わせの最大長（デフォルト: 5モーラ）
    # トークン単位でモーラの一致を図るため、そこまで長くなくてもよい
    max_mora_length: int = 5


# シングルトンインスタンス
settings = Settings()
