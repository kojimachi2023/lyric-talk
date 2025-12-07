"""
matcher.py のテスト
"""

import pytest

from src.lyric_index import LyricIndex, Token
from src.matcher import (
    Matcher,
    MatchResult,
    MatchType,
    MoraMatch,
    MoraMatchItem,
)


class TestMatchResult:
    """MatchResultクラスのテスト"""

    def test_get_output_text_exact_surface(self):
        """完全一致の場合の出力テキスト"""
        token = Token(surface="愛", reading="アイ", lemma="愛", pos="NOUN")
        result = MatchResult(
            input_token="愛",
            input_reading="アイ",
            match_type=MatchType.EXACT_SURFACE,
            matched_tokens=[token],
        )
        assert result.get_output_text() == "愛"

    def test_get_output_text_exact_reading(self):
        """読み一致の場合の出力テキスト"""
        token = Token(surface="藍", reading="アイ", lemma="藍", pos="NOUN")
        result = MatchResult(
            input_token="愛",
            input_reading="アイ",
            match_type=MatchType.EXACT_READING,
            matched_tokens=[token],
        )
        assert result.get_output_text() == "藍"

    def test_get_output_text_mora_combination(self):
        """モーラ組み合わせの場合の出力テキスト"""
        token1 = Token(surface="歩き", reading="アルキ", lemma="歩く", pos="VERB")
        token2 = Token(surface="不足", reading="フソク", lemma="不足", pos="NOUN")
        token3 = Token(surface="どこ", reading="ドコ", lemma="どこ", pos="NOUN")

        mora_items = [
            MoraMatchItem(mora="ア", source_token=token1, mora_index=0),
            MoraMatchItem(mora="ソ", source_token=token2, mora_index=1),
            MoraMatchItem(mora="コ", source_token=token3, mora_index=1),
        ]
        mora_match = MoraMatch(
            moras=["ア", "ソ", "コ"],
            source_tokens=[token1, token2, token3],
            mora_items=mora_items,
        )
        result = MatchResult(
            input_token="あそこ",
            input_reading="アソコ",
            match_type=MatchType.MORA_COMBINATION,
            mora_match=mora_match,
        )
        assert result.get_output_text() == "アソコ"

    def test_get_output_text_similar_surface(self):
        """意味的類似（表層形）の場合の出力テキスト"""
        token = Token(surface="君", reading="キミ", lemma="君", pos="NOUN")
        result = MatchResult(
            input_token="私",
            input_reading="ワタシ",
            match_type=MatchType.SIMILAR_SURFACE,
            matched_tokens=[token],
            similar_word="君",
            similarity_score=0.9,
        )
        assert result.get_output_text() == "君"

    def test_get_output_text_no_match(self):
        """マッチなしの場合の出力テキスト"""
        result = MatchResult(
            input_token="xyz",
            input_reading="XYZ",
            match_type=MatchType.NO_MATCH,
        )
        assert result.get_output_text() == ""

    def test_to_dict_exact_surface(self):
        """to_dict: 完全一致"""
        token = Token(
            surface="愛",
            reading="アイ",
            lemma="愛",
            pos="NOUN",
            line_index=0,
            token_index=0,
        )
        result = MatchResult(
            input_token="愛",
            input_reading="アイ",
            match_type=MatchType.EXACT_SURFACE,
            matched_tokens=[token],
        )
        d = result.to_dict()

        assert d["input_token"] == "愛"
        assert d["input_reading"] == "アイ"
        assert d["match_type"] == "exact_surface"
        assert len(d["matched_tokens"]) == 1
        assert d["matched_tokens"][0]["surface"] == "愛"

    def test_to_dict_mora_combination(self):
        """to_dict: モーラ組み合わせ"""
        token1 = Token(surface="歩き", reading="アルキ", lemma="歩く", pos="VERB", line_index=1)
        mora_items = [MoraMatchItem(mora="ア", source_token=token1, mora_index=0)]
        mora_match = MoraMatch(
            moras=["ア"],
            source_tokens=[token1],
            mora_items=mora_items,
        )
        result = MatchResult(
            input_token="あ",
            input_reading="ア",
            match_type=MatchType.MORA_COMBINATION,
            mora_match=mora_match,
        )
        d = result.to_dict()

        assert d["match_type"] == "mora_combination"
        assert "mora_match" in d
        assert d["mora_match"]["moras"] == ["ア"]
        assert d["mora_match"]["source_surfaces"] == ["歩き"]
        assert len(d["mora_match"]["details"]) == 1


class TestMatcher:
    """Matcherクラスのテスト"""

    @pytest.fixture
    def simple_lyric_index(self, nlp):
        """シンプルな歌詞インデックス"""
        index = LyricIndex()
        # 「愛」「を」「信じて」のトークンを追加
        index.add_token(Token(surface="愛", reading="アイ", lemma="愛", pos="NOUN", line_index=0))
        index.add_token(Token(surface="を", reading="ヲ", lemma="を", pos="ADP", line_index=0))
        index.add_token(
            Token(surface="信じ", reading="シンジ", lemma="信じる", pos="VERB", line_index=0)
        )
        index.add_token(Token(surface="て", reading="テ", lemma="て", pos="SCONJ", line_index=0))
        # モーラ検索用の追加トークン
        index.add_token(
            Token(surface="歩き", reading="アルキ", lemma="歩く", pos="VERB", line_index=1)
        )
        index.add_token(
            Token(surface="不足", reading="フソク", lemma="不足", pos="NOUN", line_index=1)
        )
        index.add_token(
            Token(surface="どこ", reading="ドコ", lemma="どこ", pos="NOUN", line_index=1)
        )
        return index

    def test_match_exact_surface(self, nlp, simple_lyric_index):
        """表層形完全一致のテスト"""
        matcher = Matcher(simple_lyric_index, nlp=nlp)
        results = matcher.match("愛")

        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT_SURFACE
        assert results[0].matched_tokens[0].surface == "愛"

    def test_match_exact_reading(self, nlp, simple_lyric_index):
        """読み完全一致のテスト"""
        # 「藍」は歌詞にないが、「アイ」という読みは「愛」にある
        matcher = Matcher(simple_lyric_index, nlp=nlp)
        results = matcher.match("藍")  # 藍の読みは「アイ」

        assert len(results) == 1
        # 表層形「藍」は歌詞にないが、読み「アイ」は「愛」と一致
        assert results[0].match_type == MatchType.EXACT_READING

    def test_match_mora_combination(self, nlp, simple_lyric_index):
        """モーラ組み合わせのテスト"""
        matcher = Matcher(simple_lyric_index, nlp=nlp)
        results = matcher.match("あそこ")  # アソコ

        assert len(results) == 1
        assert results[0].match_type == MatchType.MORA_COMBINATION
        assert results[0].mora_match is not None
        assert results[0].mora_match.moras == ["ア", "ソ", "コ"]

    def test_match_multiple_tokens(self, nlp, simple_lyric_index):
        """複数トークンのマッチング"""
        matcher = Matcher(simple_lyric_index, nlp=nlp)
        results = matcher.match("愛を信じて")

        # 少なくとも2つ以上のトークンがマッチ
        assert len(results) >= 2
        # 「愛」は完全一致
        assert any(
            r.input_token == "愛" and r.match_type == MatchType.EXACT_SURFACE for r in results
        )


class TestMatcherMoraCombination:
    """モーラ組み合わせの詳細テスト"""

    @pytest.fixture
    def mora_test_index(self, nlp):
        """モーラテスト用のインデックス"""
        index = LyricIndex()
        # 「ナ」「ル」「ホ」「ド」が取れるトークンを追加
        index.add_token(
            Token(surface="慣れ", reading="ナレ", lemma="慣れる", pos="VERB", line_index=0)
        )
        index.add_token(
            Token(surface="歩き", reading="アルキ", lemma="歩く", pos="VERB", line_index=0)
        )
        index.add_token(Token(surface="炎", reading="ホノオ", lemma="炎", pos="NOUN", line_index=0))
        index.add_token(
            Token(surface="どこ", reading="ドコ", lemma="どこ", pos="NOUN", line_index=0)
        )
        return index

    def test_mora_combination_naruhodo(self, nlp, mora_test_index):
        """「なるほど」のモーラ組み合わせ"""
        matcher = Matcher(mora_test_index, nlp=nlp)
        results = matcher.match("なるほど")  # ナルホド

        assert len(results) == 1
        assert results[0].match_type == MatchType.MORA_COMBINATION
        assert results[0].mora_match is not None
        assert len(results[0].mora_match.mora_items) == 4
        # 各モーラの元トークンを確認
        assert results[0].mora_match.mora_items[0].mora == "ナ"
        assert results[0].mora_match.mora_items[0].source_token.surface == "慣れ"

    def test_mora_combination_missing_mora(self, nlp):
        """存在しないモーラがある場合"""
        index = LyricIndex()
        # 「ア」しかない
        index.add_token(
            Token(surface="歩き", reading="アルキ", lemma="歩く", pos="VERB", line_index=0)
        )

        matcher = Matcher(index, nlp=nlp)
        results = matcher.match("あそこ")  # アソコ - 「ソ」「コ」がない

        assert len(results) == 1
        # モーラ組み合わせ不可なので、意味的類似かマッチなし
        assert results[0].match_type in (
            MatchType.SIMILAR_SURFACE,
            MatchType.SIMILAR_READING,
            MatchType.SIMILAR_MORA,
            MatchType.NO_MATCH,
        )
