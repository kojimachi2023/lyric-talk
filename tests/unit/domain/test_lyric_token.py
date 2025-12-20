"""
Test module for LyricToken entity
Tests are written BEFORE implementation (TDD Red phase)
"""

from src.domain.models.lyric_token import LyricToken
from src.domain.models.mora import Mora
from src.domain.models.reading import Reading


class TestLyricToken:
    """LyricTokenエンティティのテスト"""

    def test_lyric_token_creation(self):
        """LyricTokenを作成できることを確認"""
        reading = Reading(raw="とうきょう")
        token = LyricToken(
            lyrics_corpus_id="test_corpus_001",
            surface="東京",
            reading=reading,
            lemma="東京",
            pos="名詞",
            line_index=0,
            token_index=1,
        )
        assert token.lyrics_corpus_id == "test_corpus_001"
        assert token.surface == "東京"
        assert token.reading == reading
        assert token.lemma == "東京"
        assert token.pos == "名詞"
        assert token.line_index == 0
        assert token.token_index == 1

    def test_token_id_property(self):
        """token_idプロパティが正しいフォーマットで返されることを確認"""
        reading = Reading(raw="とうきょう")
        token = LyricToken(
            lyrics_corpus_id="test_corpus_001",
            surface="東京",
            reading=reading,
            lemma="東京",
            pos="名詞",
            line_index=2,
            token_index=3,
        )
        # フォーマット: {lyrics_corpus_id}_{line_index}_{token_index}
        assert token.token_id == "test_corpus_001_2_3"

    def test_token_id_with_different_indices(self):
        """異なるインデックスでtoken_idが正しく生成されることを確認"""
        reading = Reading(raw="きょうと")
        token = LyricToken(
            lyrics_corpus_id="corpus_abc",
            surface="京都",
            reading=reading,
            lemma="京都",
            pos="名詞",
            line_index=10,
            token_index=5,
        )
        assert token.token_id == "corpus_abc_10_5"

    def test_moras_property(self):
        """morasプロパティがMoraのリストを返すことを確認"""
        reading = Reading(raw="とうきょう")
        token = LyricToken(
            lyrics_corpus_id="test_corpus_001",
            surface="東京",
            reading=reading,
            lemma="東京",
            pos="名詞",
            line_index=0,
            token_index=0,
        )
        moras = token.moras
        assert isinstance(moras, list)
        assert all(isinstance(m, Mora) for m in moras)
        # "トウキョウ" → ["ト", "ウ", "キョ", "ウ"]
        assert len(moras) == 4
        assert [m.value for m in moras] == ["ト", "ウ", "キョ", "ウ"]

    def test_moras_property_with_different_reading(self):
        """異なる読みでmorasプロパティが正しく動作することを確認"""
        reading = Reading(raw="がっこう")
        token = LyricToken(
            lyrics_corpus_id="test_corpus_002",
            surface="学校",
            reading=reading,
            lemma="学校",
            pos="名詞",
            line_index=1,
            token_index=2,
        )
        moras = token.moras
        # "ガッコウ" → ["ガ", "ッ", "コ", "ウ"]
        assert len(moras) == 4
        assert [m.value for m in moras] == ["ガ", "ッ", "コ", "ウ"]

    def test_lyric_token_mutability(self):
        """LyricTokenはエンティティなので可変であることを確認"""
        reading = Reading(raw="てすと")
        token = LyricToken(
            lyrics_corpus_id="test_corpus_003",
            surface="テスト",
            reading=reading,
            lemma="テスト",
            pos="名詞",
            line_index=0,
            token_index=0,
        )
        # エンティティは可変なので属性を変更できる
        token.surface = "試験"
        assert token.surface == "試験"

    def test_lyric_token_with_hiragana_reading(self):
        """ひらがなの読みでもmorasが正しく生成されることを確認"""
        reading = Reading(raw="さくら")
        token = LyricToken(
            lyrics_corpus_id="test_corpus_004",
            surface="桜",
            reading=reading,
            lemma="桜",
            pos="名詞",
            line_index=0,
            token_index=0,
        )
        moras = token.moras
        # "さくら" → "サクラ" → ["サ", "ク", "ラ"]
        assert len(moras) == 3
        assert [m.value for m in moras] == ["サ", "ク", "ラ"]

    def test_lyric_token_with_youon(self):
        """拗音を含む読みでmorasが正しく生成されることを確認"""
        reading = Reading(raw="きょう")
        token = LyricToken(
            lyrics_corpus_id="test_corpus_005",
            surface="今日",
            reading=reading,
            lemma="今日",
            pos="名詞",
            line_index=0,
            token_index=0,
        )
        moras = token.moras
        # "きょう" → "キョウ" → ["キョ", "ウ"]
        assert len(moras) == 2
        assert [m.value for m in moras] == ["キョ", "ウ"]

    def test_token_id_zero_indices(self):
        """インデックスがゼロの場合のtoken_idを確認"""
        reading = Reading(raw="てすと")
        token = LyricToken(
            lyrics_corpus_id="corpus_zero",
            surface="テスト",
            reading=reading,
            lemma="テスト",
            pos="名詞",
            line_index=0,
            token_index=0,
        )
        assert token.token_id == "corpus_zero_0_0"
