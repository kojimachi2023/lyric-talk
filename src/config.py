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

    # 意味的類似度の閾値（デフォルト: 0.5）
    # この値以上の類似度で「類似」と判定する
    similarity_threshold: float = 0.8

    # 類似語検索の上限数
    max_similar_words: int = 5

    # sentence-transformersのモデル名
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"


# シングルトンインスタンス
settings = Settings()
