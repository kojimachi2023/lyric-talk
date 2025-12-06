"""
歌詞インデックス: 歌詞を解析し、単語・モーラ・読みを保持する
spaCy + GiNZAを使用して日本語形態素解析を行う
"""

from dataclasses import dataclass, field

import spacy

from .mora import normalize_reading, split_mora


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
    """

    tokens: list[Token] = field(default_factory=list)
    surface_to_tokens: dict[str, list[Token]] = field(default_factory=dict)
    reading_to_tokens: dict[str, list[Token]] = field(default_factory=dict)
    mora_set: set[str] = field(default_factory=set)
    mora_to_tokens: dict[str, list[Token]] = field(default_factory=dict)

    @classmethod
    def from_lyrics(cls, lyrics: str, nlp: spacy.Language | None = None) -> "LyricIndex":
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
        lines = lyrics.strip().split("\n")

        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            doc = nlp(line)
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
