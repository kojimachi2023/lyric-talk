"""
lyric_index.py のテスト
"""

import pytest

from src.lyric_index import LyricIndex, Token


class TestToken:
    """Tokenクラスのテスト"""

    def test_token_creation(self):
        """トークン作成のテスト"""
        token = Token(
            surface="歩き",
            reading="アルキ",
            lemma="歩く",
            pos="VERB",
            line_index=0,
            token_index=0,
        )
        assert token.surface == "歩き"
        assert token.reading == "アルキ"
        assert token.lemma == "歩く"
        assert token.pos == "VERB"

    def test_token_mora_auto_generation(self):
        """読みからモーラが自動生成されることのテスト"""
        token = Token(
            surface="東京",
            reading="トウキョウ",
            lemma="東京",
            pos="NOUN",
        )
        assert token.moras == ["ト", "ウ", "キョ", "ウ"]

    def test_token_empty_reading(self):
        """読みが空の場合"""
        token = Token(
            surface="test",
            reading="",
            lemma="test",
            pos="NOUN",
        )
        assert token.moras == []


class TestLyricIndex:
    """LyricIndexクラスのテスト"""

    def test_add_token(self):
        """トークン追加のテスト"""
        index = LyricIndex()
        token = Token(
            surface="愛",
            reading="アイ",
            lemma="愛",
            pos="NOUN",
            line_index=0,
            token_index=0,
        )
        index.add_token(token)

        assert len(index.tokens) == 1
        assert "愛" in index.surface_to_tokens
        assert "アイ" in index.reading_to_tokens
        assert "ア" in index.mora_set
        assert "イ" in index.mora_set

    def test_find_by_surface(self):
        """表層形での検索テスト"""
        index = LyricIndex()
        token = Token(
            surface="愛",
            reading="アイ",
            lemma="愛",
            pos="NOUN",
        )
        index.add_token(token)

        result = index.find_by_surface("愛")
        assert len(result) == 1
        assert result[0].surface == "愛"

        result = index.find_by_surface("恋")
        assert len(result) == 0

    def test_find_by_reading(self):
        """読みでの検索テスト"""
        index = LyricIndex()
        token = Token(
            surface="愛",
            reading="アイ",
            lemma="愛",
            pos="NOUN",
        )
        index.add_token(token)

        result = index.find_by_reading("アイ")
        assert len(result) == 1
        assert result[0].reading == "アイ"

    def test_find_by_mora(self):
        """モーラでの検索テスト"""
        index = LyricIndex()
        token = Token(
            surface="愛",
            reading="アイ",
            lemma="愛",
            pos="NOUN",
        )
        index.add_token(token)

        result = index.find_by_mora("ア")
        assert len(result) == 1
        assert result[0].surface == "愛"

    def test_has_mora(self):
        """モーラ存在チェックのテスト"""
        index = LyricIndex()
        token = Token(
            surface="愛",
            reading="アイ",
            lemma="愛",
            pos="NOUN",
        )
        index.add_token(token)

        assert index.has_mora("ア") is True
        assert index.has_mora("イ") is True
        assert index.has_mora("ウ") is False

    def test_get_all_surfaces(self):
        """全表層形取得のテスト"""
        index = LyricIndex()
        index.add_token(Token(surface="愛", reading="アイ", lemma="愛", pos="NOUN"))
        index.add_token(Token(surface="恋", reading="コイ", lemma="恋", pos="NOUN"))

        surfaces = index.get_all_surfaces()
        assert surfaces == {"愛", "恋"}

    def test_get_all_readings(self):
        """全読み取得のテスト"""
        index = LyricIndex()
        index.add_token(Token(surface="愛", reading="アイ", lemma="愛", pos="NOUN"))
        index.add_token(Token(surface="恋", reading="コイ", lemma="恋", pos="NOUN"))

        readings = index.get_all_readings()
        assert readings == {"アイ", "コイ"}

    def test_multiple_tokens_same_surface(self):
        """同じ表層形の複数トークン"""
        index = LyricIndex()
        token1 = Token(surface="愛", reading="アイ", lemma="愛", pos="NOUN", line_index=0)
        token2 = Token(surface="愛", reading="アイ", lemma="愛", pos="NOUN", line_index=1)
        index.add_token(token1)
        index.add_token(token2)

        result = index.find_by_surface("愛")
        assert len(result) == 2


class TestLyricIndexFromLyrics:
    """LyricIndex.from_lyrics のテスト（spaCy依存）"""

    @pytest.fixture
    def nlp(self):
        """spaCy + GiNZAモデルをロード"""
        import spacy

        return spacy.load("ja_ginza")

    def test_from_lyrics_basic(self, nlp):
        """基本的な歌詞からのインデックス構築"""
        lyrics = "愛を信じて"
        index = LyricIndex.from_lyrics(lyrics, nlp=nlp)

        assert len(index.tokens) > 0
        assert "愛" in index.surface_to_tokens

    def test_from_lyrics_multiline(self, nlp):
        """複数行の歌詞からのインデックス構築"""
        lyrics = """愛を信じて
空を見上げて
夢を追いかけて"""
        index = LyricIndex.from_lyrics(lyrics, nlp=nlp)

        assert len(index.tokens) > 0
        # 複数の行からトークンが取得されていることを確認
        line_indices = {t.line_index for t in index.tokens}
        assert len(line_indices) >= 2

    def test_from_lyrics_empty(self, nlp):
        """空の歌詞"""
        lyrics = ""
        index = LyricIndex.from_lyrics(lyrics, nlp=nlp)
        assert len(index.tokens) == 0

    def test_from_lyrics_whitespace_only(self, nlp):
        """空白のみの歌詞"""
        lyrics = "   \n   \n   "
        index = LyricIndex.from_lyrics(lyrics, nlp=nlp)
        assert len(index.tokens) == 0
