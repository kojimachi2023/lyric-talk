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

    # sentence-transformersのモデル名（後方互換性のため残す）
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # 文脈考慮型埋め込みに使用するtransformerモデル
    transformer_model: str = "cl-nagoya/ruri-v3-310m"

    # 隠れ状態抽出レイヤー（-1は最終層）
    hidden_layer: int = -1

    # プーリング方式（"mean": 平均プーリング, "first": 最初のトークン, "last": 最後のトークン）
    pooling_strategy: str = "mean"

    # 内容語の品詞リスト（これらの品詞のみ意味的類似マッチング対象）
    content_pos_tags: list[str] = [
        "NOUN",  # 名詞
        "VERB",  # 動詞
        "ADJ",  # 形容詞
        "ADV",  # 副詞
        "PROPN",  # 固有名詞
        "NUM",  # 数詞
    ]

    # ChromaDBの永続化パス（テスト時は一時ディレクトリに上書き可能）
    chromadb_path: str = "chroma_db"

    # ChromaDBコレクション名のプレフィックス
    chromadb_collection: str = "lyric_embeddings"

    # ChromaDBコレクション名にタイムスタンプを付与するか
    # True: 毎回新しいコレクションを作成（前回データは残らない）
    # False: 固定名のコレクションを再利用（前回データが残る）
    chromadb_use_timestamp: bool = True


# シングルトンインスタンス
settings = Settings()
