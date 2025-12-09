"""
歌詞インデックス: 歌詞を解析し、単語・モーラ・読みを保持する
spaCy + GiNZAを使用して日本語形態素解析を行う
ChromaDBを使用して文脈考慮型埋め込みを保存・検索
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import chromadb
import spacy

from .config import settings
from .mora import normalize_reading, split_mora
from .token_alignment import TokenAligner


@dataclass
class Token:
    """トークン情報"""

    surface: str  # 表層形（元の文字列）
    reading: str  # 読み（カタカナ）
    lemma: str  # 基本形
    pos: str  # 品詞
    moras: list[str] = field(default_factory=list)  # モーラ分割結果
    line_index: int = 0  # 歌詞の行番号
    token_index: int = 0  # 行内のトークン番号

    def __post_init__(self) -> None:
        """読みからモーラを自動生成"""
        if self.reading and not self.moras:
            self.moras = split_mora(self.reading)


@dataclass
class LyricIndex:
    """
    歌詞インデックス

    歌詞を解析し、以下の情報を保持:
    - tokens: 全トークンのリスト
    - surface_to_tokens: 表層形からトークンへのマッピング
    - reading_to_tokens: 読みからトークンへのマッピング
    - mora_set: 歌詞に含まれる全モーラのセット（高速検索用）
    - mora_to_tokens: モーラからトークンへのマッピング
    - chroma_client: ChromaDBクライアント（文脈埋め込み用）
    - chroma_collection: ChromaDBコレクション
    - token_aligner: トークンアライメントユーティリティ
    """

    tokens: list[Token] = field(default_factory=list)
    surface_to_tokens: dict[str, list[Token]] = field(default_factory=dict)
    reading_to_tokens: dict[str, list[Token]] = field(default_factory=dict)
    mora_set: set[str] = field(default_factory=set)
    mora_to_tokens: dict[str, list[Token]] = field(default_factory=dict)
    chroma_client: chromadb.Client | None = None
    chroma_collection: chromadb.Collection | None = None
    token_aligner: TokenAligner | None = None

    @classmethod
    def from_lyrics(
        cls,
        lyrics: str,
        nlp: spacy.Language | None = None,
    ) -> "LyricIndex":
        """
        歌詞文字列からLyricIndexを構築する

        Args:
            lyrics: 歌詞文字列（改行区切り）
            nlp: spaCyのLanguageオブジェクト（Noneの場合は自動ロード）

        Returns:
            構築されたLyricIndex
        """
        if nlp is None:
            nlp = spacy.load("ja_ginza")

        index = cls()

        # 文脈埋め込みを使用する場合、ChromaDBとTokenAlignerを初期化
        index._init_chromadb()
        index.token_aligner = TokenAligner(
            transformer_model_name=settings.embedding_model,
            hidden_layer=settings.hidden_layer,
            pooling_strategy=settings.pooling_strategy,
        )

        lines = lyrics.strip().split("\n")

        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            doc = nlp(line)

            # 文脈埋め込みを計算（行単位）
            aligned_embeddings = None
            if index.token_aligner:
                aligned_embeddings = index.token_aligner.align_and_extract(line, doc)
            else:
                aligned_embeddings = []

            # アライメント結果をspaCyトークンインデックスでマッピング
            embedding_map = {}
            if aligned_embeddings:
                for aligned in aligned_embeddings:
                    embedding_map[aligned.spacy_token_index] = aligned.embedding

            for token_idx, spacy_token in enumerate(doc):
                # 空白・記号をスキップ
                if spacy_token.is_space or spacy_token.is_punct:
                    continue

                # 読みを取得（GiNZAはinflフィールドに読みを持つことがある）
                # morph.get("Reading")で読みを取得
                reading_list = spacy_token.morph.get("Reading")
                reading = reading_list[0] if reading_list else ""

                # 読みが取得できない場合は表層形をカタカナとして使用
                if not reading:
                    reading = normalize_reading(spacy_token.text)

                token = Token(
                    surface=spacy_token.text,
                    reading=reading,
                    lemma=spacy_token.lemma_,
                    pos=spacy_token.pos_,
                    line_index=line_idx,
                    token_index=token_idx,
                )

                index.add_token(token)

                # 文脈埋め込みをChromaDBに保存（機能語のみ）
                if token.pos in settings.content_pos_tags and spacy_token.i in embedding_map:
                    index._add_embedding_to_chromadb(token, embedding_map[spacy_token.i])

        return index

    def add_token(self, token: Token) -> None:
        """トークンをインデックスに追加"""
        self.tokens.append(token)

        # 表層形マッピング
        if token.surface not in self.surface_to_tokens:
            self.surface_to_tokens[token.surface] = []
        self.surface_to_tokens[token.surface].append(token)

        # 読みマッピング
        if token.reading:
            if token.reading not in self.reading_to_tokens:
                self.reading_to_tokens[token.reading] = []
            self.reading_to_tokens[token.reading].append(token)

        # モーラ処理
        for mora in token.moras:
            self.mora_set.add(mora)
            if mora not in self.mora_to_tokens:
                self.mora_to_tokens[mora] = []
            self.mora_to_tokens[mora].append(token)

    def find_by_surface(self, surface: str) -> list[Token]:
        """表層形で検索"""
        return self.surface_to_tokens.get(surface, [])

    def find_by_reading(self, reading: str) -> list[Token]:
        """読みで検索"""
        normalized = normalize_reading(reading)
        return self.reading_to_tokens.get(normalized, [])

    def find_by_mora(self, mora: str) -> list[Token]:
        """モーラで検索"""
        return self.mora_to_tokens.get(mora, [])

    def has_mora(self, mora: str) -> bool:
        """モーラが存在するかチェック"""
        return mora in self.mora_set

    def get_all_surfaces(self) -> set[str]:
        """全ての表層形を取得"""
        return set(self.surface_to_tokens.keys())

    def get_all_readings(self) -> set[str]:
        """全ての読みを取得"""
        return set(self.reading_to_tokens.keys())

    def _init_chromadb(self) -> None:
        """ChromaDBを初期化"""

        # 永続化ディレクトリを作成
        persist_dir = Path(settings.chromadb_path)
        persist_dir.mkdir(parents=True, exist_ok=True)

        # ChromaDBクライアントを初期化
        self.chroma_client = chromadb.PersistentClient(path=str(persist_dir))

        # コレクション名を生成（タイムスタンプ付きか固定名）
        if settings.chromadb_use_timestamp:
            # タイムスタンプ付きコレクション名で毎回新規作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            collection_name = f"{settings.chromadb_collection}_{timestamp}"
        else:
            # 固定名のコレクションを使用（既存があれば再利用）
            collection_name = settings.chromadb_collection

        # コレクションを取得または作成
        try:
            self.chroma_collection = self.chroma_client.get_collection(name=collection_name)
        except Exception:
            # コレクションが存在しない場合は新規作成
            self.chroma_collection = self.chroma_client.create_collection(
                name=collection_name,
                configuration={"hnsw": {"space": "cosine"}},
                metadata={"description": "Contextual embeddings for lyric tokens"},
            )

    def _add_embedding_to_chromadb(self, token: Token, embedding: list[float]) -> None:
        """
        トークンの文脈埋め込みをChromaDBに保存

        Args:
            token: トークン情報
            embedding: 文脈埋め込みベクトル
        """
        if not self.chroma_collection:
            return

        # ユニークIDを生成
        token_id = f"{token.line_index}_{token.token_index}_{token.surface}"

        # メタデータ
        metadata = {
            "surface": token.surface,
            "reading": token.reading,
            "lemma": token.lemma,
            "pos": token.pos,
            "line_index": token.line_index,
            "token_index": token.token_index,
        }

        # ChromaDBに追加
        self.chroma_collection.add(
            ids=[token_id],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def query_similar_tokens(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        pos_filter: str | None = None,
    ) -> list[tuple[float, Token]]:
        """
        文脈埋め込みから類似トークンを検索

        Args:
            query_embedding: クエリの文脈埋め込み
            n_results: 返す結果の数
            pos_filter: 品詞フィルタ（Noneの場合はフィルタなし）

        Returns:
            (類似度, 類似トークン)のリスト
        """
        if not self.chroma_collection:
            return []

        # 品詞フィルタを適用
        where_filter = None
        if pos_filter:
            where_filter = {"pos": pos_filter}

        # クエリ実行
        results = self.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
        )

        if not results or len(results["ids"]) == 0:
            return []

        # 結果をTokenオブジェクトに変換
        similar_tokens = [
            (
                results["distances"][0][i],
                Token(
                    surface=results["metadatas"][0][i]["surface"],
                    reading=results["metadatas"][0][i]["reading"],
                    lemma=results["metadatas"][0][i]["lemma"],
                    pos=results["metadatas"][0][i]["pos"],
                    line_index=results["metadatas"][0][i]["line_index"],
                    token_index=results["metadatas"][0][i]["token_index"],
                ),
            )
            for i in range(len(results["ids"][0]))
        ]

        return similar_tokens
