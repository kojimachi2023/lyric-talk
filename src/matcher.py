"""
マッチングエンジン: 入力文章を歌詞素材から再現するためのマッチング処理

マッチング優先度:
1. 単語の完全一致（表層形）
2. 読みの完全一致
3. モーラ（音節）の組み合わせ一致
4. 意味的類似一致（類似語を見つけた後、上記1-3のループを再度試す）
"""

from dataclasses import dataclass, field
from enum import Enum

import spacy
from sentence_transformers import SentenceTransformer

from .config import settings
from .lyric_index import LyricIndex, Token
from .mora import normalize_reading, split_mora


class MatchType(str, Enum):
    """マッチタイプ"""

    EXACT_SURFACE = "exact_surface"  # 表層形完全一致
    EXACT_READING = "exact_reading"  # 読み完全一致
    MORA_COMBINATION = "mora_combination"  # モーラ組み合わせ
    SIMILAR_SURFACE = "similar_surface"  # 類似語の表層形一致
    SIMILAR_READING = "similar_reading"  # 類似語の読み一致
    SIMILAR_MORA = "similar_mora"  # 類似語のモーラ組み合わせ
    NO_MATCH = "no_match"  # マッチなし


@dataclass
class MoraMatchItem:
    """個々のモーラのマッチ情報"""

    mora: str  # マッチしたモーラ
    source_token: Token  # 元になったトークン
    mora_index: int  # トークン内でのモーラ位置


@dataclass
class MoraMatch:
    """モーラ組み合わせのマッチ結果"""

    moras: list[str]  # マッチしたモーラのリスト
    source_tokens: list[Token]  # 元になったトークンのリスト（後方互換用）
    mora_items: list[MoraMatchItem] = field(default_factory=list)  # 詳細情報


@dataclass
class MatchResult:
    """マッチング結果"""

    input_token: str  # 入力トークン（表層形）
    input_reading: str  # 入力トークン（読み）
    match_type: MatchType  # マッチタイプ
    matched_tokens: list[Token] = field(default_factory=list)  # マッチしたトークン
    mora_match: MoraMatch | None = None  # モーラ組み合わせの場合
    similar_word: str | None = None  # 類似語（類似マッチの場合）
    similarity_score: float | None = None  # 類似度スコア

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        result = {
            "input_token": self.input_token,
            "input_reading": self.input_reading,
            "match_type": self.match_type.value,
        }

        if self.matched_tokens:
            result["matched_tokens"] = [
                {
                    "surface": t.surface,
                    "reading": t.reading,
                    "line_index": t.line_index,
                    "token_index": t.token_index,
                }
                for t in self.matched_tokens
            ]

        if self.mora_match:
            result["mora_match"] = {
                "moras": self.mora_match.moras,
                "source_surfaces": [t.surface for t in self.mora_match.source_tokens],
                "details": [
                    {
                        "mora": item.mora,
                        "source_surface": item.source_token.surface,
                        "source_reading": item.source_token.reading,
                        "mora_index": item.mora_index,
                        "line_index": item.source_token.line_index,
                    }
                    for item in self.mora_match.mora_items
                ],
            }

        if self.similar_word:
            result["similar_word"] = self.similar_word

        if self.similarity_score is not None:
            result["similarity_score"] = self.similarity_score

        return result

    def get_output_text(self) -> str:
        """
        マッチング結果から出力テキストを生成する

        マッチタイプに応じて適切な文字列を返す:
        - 完全一致/読み一致: マッチしたトークンの表層形
        - モーラ組み合わせ: 各モーラの元トークンの表層形を連結
        - 意味的類似: 類似語としてマッチしたトークンの表層形
        - マッチなし: 空文字列
        """
        if self.match_type == MatchType.NO_MATCH:
            return ""

        if self.match_type == MatchType.MORA_COMBINATION:
            # モーラ組み合わせの場合、各モーラを組み合わせて出力
            if self.mora_match and self.mora_match.mora_items:
                return "".join(item.mora for item in self.mora_match.mora_items)
            return ""

        if self.match_type in (MatchType.SIMILAR_MORA,):
            # 意味的類似のモーラ組み合わせ
            if self.mora_match and self.mora_match.mora_items:
                return "".join(item.source_token.surface for item in self.mora_match.mora_items)
            return ""

        # 完全一致、読み一致、意味的類似（表層形/読み）
        if self.matched_tokens:
            return self.matched_tokens[0].surface

        return ""


class Matcher:
    """
    マッチングエンジン

    入力文章のトークンを歌詞素材から最適にマッチングする
    """

    def __init__(
        self,
        lyric_index: LyricIndex,
        nlp: spacy.Language | None = None,
        embedding_model: SentenceTransformer | None = None,
    ):
        self.lyric_index = lyric_index
        self.nlp = nlp or spacy.load("ja_ginza")
        self.embedding_model = embedding_model or SentenceTransformer(settings.embedding_model)

        # 歌詞の全単語の埋め込みを事前計算
        self._precompute_embeddings()

    def _precompute_embeddings(self) -> None:
        """歌詞の全単語の埋め込みを事前計算"""
        surfaces = list(self.lyric_index.get_all_surfaces())
        if surfaces:
            self.surface_embeddings = self.embedding_model.encode(surfaces, convert_to_tensor=True)
            self.surface_list = surfaces
        else:
            self.surface_embeddings = None
            self.surface_list = []

    def match(self, text: str) -> list[MatchResult]:
        """
        テキストをマッチングする

        Args:
            text: 入力テキスト

        Returns:
            各トークンのマッチング結果のリスト
        """
        doc = self.nlp(text)
        results = []

        for spacy_token in doc:
            # 空白・記号をスキップ
            if spacy_token.is_space or spacy_token.is_punct:
                continue

            # 読みを取得
            reading_list = spacy_token.morph.get("Reading")
            reading = reading_list[0] if reading_list else ""
            if not reading:
                reading = normalize_reading(spacy_token.text)

            result = self._match_token(spacy_token.text, reading)
            results.append(result)

        return results

    def _match_token(self, surface: str, reading: str) -> MatchResult:
        """
        単一トークンをマッチングする

        優先度:
        1. 表層形完全一致
        2. 読み完全一致
        3. モーラ組み合わせ
        4. 意味的類似 → 上記1-3を類似語で再試行
        """
        # 1. 表層形完全一致
        tokens = self.lyric_index.find_by_surface(surface)
        if tokens:
            return MatchResult(
                input_token=surface,
                input_reading=reading,
                match_type=MatchType.EXACT_SURFACE,
                matched_tokens=tokens[:1],  # 最初の1つを使用
            )

        # 2. 読み完全一致
        tokens = self.lyric_index.find_by_reading(reading)
        if tokens:
            return MatchResult(
                input_token=surface,
                input_reading=reading,
                match_type=MatchType.EXACT_READING,
                matched_tokens=tokens[:1],
            )

        # 3. モーラ組み合わせ
        mora_match = self._find_mora_combination(reading)
        if mora_match:
            return MatchResult(
                input_token=surface,
                input_reading=reading,
                match_type=MatchType.MORA_COMBINATION,
                mora_match=mora_match,
            )

        # 4. 意味的類似
        similar_result = self._find_similar_match(surface, reading)
        if similar_result:
            return similar_result

        # マッチなし
        return MatchResult(
            input_token=surface,
            input_reading=reading,
            match_type=MatchType.NO_MATCH,
        )

    def _find_mora_combination(self, reading: str) -> MoraMatch | None:
        """
        モーラ組み合わせでマッチングする（動的計画法）

        個々のモーラ単位で歌詞中のトークンからマッチングを行う。
        同じトークンから複数のモーラを抽出することも許可する。

        Args:
            reading: 読み（カタカナ）

        Returns:
            マッチした場合はMoraMatch、なければNone
        """
        target_moras = split_mora(reading)
        n = len(target_moras)

        if n == 0:
            return None

        # モーラ数が設定値を超える場合はスキップ
        if n > settings.max_mora_length:
            return None

        # まず、全てのモーラが歌詞中に存在するかチェック（高速判定）
        for mora in target_moras:
            if not self.lyric_index.has_mora(mora):
                return None

        # DPテーブル: dp[i] = (i番目までマッチ可能か, 使用したMoraMatchItemリスト)
        dp: list[tuple[bool, list[MoraMatchItem]]] = [(False, []) for _ in range(n + 1)]
        dp[0] = (True, [])

        for i in range(n):
            if not dp[i][0]:
                continue

            # 方式1: 個々のモーラを1つずつマッチング
            mora = target_moras[i]
            tokens = self.lyric_index.find_by_mora(mora)
            if tokens:
                # 最初に見つかったトークンを使用
                token = tokens[0]
                # トークン内でのモーラ位置を取得
                mora_index = token.moras.index(mora) if mora in token.moras else 0
                item = MoraMatchItem(mora=mora, source_token=token, mora_index=mora_index)
                if not dp[i + 1][0]:
                    dp[i + 1] = (True, dp[i][1] + [item])

            # 方式2: 複数モーラをまとめてマッチング（トークン全体の読みと一致する場合）
            for j in range(i + 2, min(i + settings.max_mora_length + 1, n + 1)):
                if dp[j][0]:
                    continue  # 既にマッチ済みならスキップ

                partial_moras = target_moras[i:j]
                partial_mora_str = "".join(partial_moras)

                # この部分モーラ列と完全一致するトークンを探す
                tokens = self.lyric_index.find_by_reading(partial_mora_str)
                if tokens:
                    token = tokens[0]
                    # 複数モーラを1つのトークンでカバー
                    items = [
                        MoraMatchItem(mora=m, source_token=token, mora_index=idx)
                        for idx, m in enumerate(partial_moras)
                    ]
                    dp[j] = (True, dp[i][1] + items)

        if dp[n][0]:
            mora_items = dp[n][1]
            source_tokens = [item.source_token for item in mora_items]
            return MoraMatch(
                moras=target_moras,
                source_tokens=source_tokens,
                mora_items=mora_items,
            )

        return None

    def _find_similar_match(self, surface: str, reading: str) -> MatchResult | None:
        """
        意味的に類似した単語を見つけ、それを使ってマッチングを試みる

        類似語が見つかった場合:
        1. 類似語の表層形が歌詞にあるか
        2. 類似語の読みが歌詞にあるか
        3. 類似語のモーラ組み合わせが可能か
        """
        if not self.surface_list:
            return None

        # 入力単語の埋め込み
        input_embedding = self.embedding_model.encode([surface], convert_to_tensor=True)

        # コサイン類似度を計算
        similarities = self.embedding_model.similarity(input_embedding, self.surface_embeddings)[0]

        # 類似度が閾値以上の単語を取得（自分自身を除く）
        similar_words = []
        for idx, sim in enumerate(similarities):
            sim_value = float(sim)
            word = self.surface_list[idx]
            if word != surface and sim_value >= settings.similarity_threshold:
                similar_words.append((word, sim_value))

        # 類似度でソート
        similar_words.sort(key=lambda x: x[1], reverse=True)
        similar_words = similar_words[: settings.max_similar_words]

        for similar_word, sim_score in similar_words:
            # 類似語の読みを取得
            doc = self.nlp(similar_word)
            if not doc:
                continue

            similar_reading = ""
            for token in doc:
                reading_list = token.morph.get("Reading")
                if reading_list:
                    similar_reading = reading_list[0]
                    break
            if not similar_reading:
                similar_reading = normalize_reading(similar_word)

            # 1. 類似語の表層形が歌詞にあるか
            tokens = self.lyric_index.find_by_surface(similar_word)
            if tokens:
                return MatchResult(
                    input_token=surface,
                    input_reading=reading,
                    match_type=MatchType.SIMILAR_SURFACE,
                    matched_tokens=tokens[:1],
                    similar_word=similar_word,
                    similarity_score=sim_score,
                )

            # 2. 類似語の読みが歌詞にあるか
            tokens = self.lyric_index.find_by_reading(similar_reading)
            if tokens:
                return MatchResult(
                    input_token=surface,
                    input_reading=reading,
                    match_type=MatchType.SIMILAR_READING,
                    matched_tokens=tokens[:1],
                    similar_word=similar_word,
                    similarity_score=sim_score,
                )

            # 3. 類似語のモーラ組み合わせが可能か
            mora_match = self._find_mora_combination(similar_reading)
            if mora_match:
                return MatchResult(
                    input_token=surface,
                    input_reading=reading,
                    match_type=MatchType.SIMILAR_MORA,
                    mora_match=mora_match,
                    similar_word=similar_word,
                    similarity_score=sim_score,
                )

        return None
