"""
mora.py のテスト
"""

from src.mora import (
    hiragana_to_katakana,
    katakana_to_hiragana,
    normalize_reading,
    split_mora,
)


class TestSplitMora:
    """split_mora関数のテスト"""

    def test_basic_katakana(self):
        """基本的なカタカナの分割"""
        assert split_mora("アイウエオ") == ["ア", "イ", "ウ", "エ", "オ"]

    def test_youon(self):
        """拗音（キャ、シュ、チョ等）のテスト"""
        assert split_mora("キャット") == ["キャ", "ッ", "ト"]
        # 注: 現在の実装では長音は前の拗音に付く（シュー = 1モーラ扱い）
        assert split_mora("シュート") == ["シュー", "ト"]
        assert split_mora("チョコ") == ["チョ", "コ"]

    def test_sokuon(self):
        """促音（ッ）のテスト"""
        assert split_mora("カット") == ["カ", "ッ", "ト"]
        assert split_mora("バッグ") == ["バ", "ッ", "グ"]

    def test_hatsuon(self):
        """撥音（ン）のテスト"""
        assert split_mora("サンポ") == ["サ", "ン", "ポ"]
        assert split_mora("ニホン") == ["ニ", "ホ", "ン"]

    def test_chouon(self):
        """長音（ー）のテスト"""
        assert split_mora("カー") == ["カー"]
        assert split_mora("スーパー") == ["スー", "パー"]

    def test_small_vowels(self):
        """小さい母音（ファ、ティ等）のテスト"""
        assert split_mora("ファイル") == ["ファ", "イ", "ル"]
        # 注: 現在の実装では長音は前の小文字母音に付く（ティー = 1モーラ扱い）
        assert split_mora("ティー") == ["ティー"]

    def test_tokyo(self):
        """「トウキョウ」の分割"""
        assert split_mora("トウキョウ") == ["ト", "ウ", "キョ", "ウ"]

    def test_fighting(self):
        """「ファイティング」の分割"""
        assert split_mora("ファイティング") == ["ファ", "イ", "ティ", "ン", "グ"]

    def test_empty_string(self):
        """空文字列のテスト"""
        assert split_mora("") == []

    def test_single_mora(self):
        """単一モーラのテスト"""
        assert split_mora("ア") == ["ア"]
        assert split_mora("ン") == ["ン"]
        assert split_mora("ッ") == ["ッ"]


class TestHiraganaToKatakana:
    """hiragana_to_katakana関数のテスト"""

    def test_basic_conversion(self):
        """基本的なひらがな→カタカナ変換"""
        assert hiragana_to_katakana("あいうえお") == "アイウエオ"

    def test_mixed_text(self):
        """混在テキストの変換"""
        assert hiragana_to_katakana("あいABC") == "アイABC"

    def test_already_katakana(self):
        """既にカタカナの場合"""
        assert hiragana_to_katakana("アイウ") == "アイウ"

    def test_empty_string(self):
        """空文字列"""
        assert hiragana_to_katakana("") == ""


class TestKatakanaToHiragana:
    """katakana_to_hiragana関数のテスト"""

    def test_basic_conversion(self):
        """基本的なカタカナ→ひらがな変換"""
        assert katakana_to_hiragana("アイウエオ") == "あいうえお"

    def test_mixed_text(self):
        """混在テキストの変換"""
        assert katakana_to_hiragana("アイABC") == "あいABC"

    def test_already_hiragana(self):
        """既にひらがなの場合"""
        assert katakana_to_hiragana("あいう") == "あいう"

    def test_empty_string(self):
        """空文字列"""
        assert katakana_to_hiragana("") == ""


class TestNormalizeReading:
    """normalize_reading関数のテスト"""

    def test_hiragana_to_katakana(self):
        """ひらがなをカタカナに正規化"""
        assert normalize_reading("あいうえお") == "アイウエオ"

    def test_already_katakana(self):
        """既にカタカナの場合はそのまま"""
        assert normalize_reading("アイウエオ") == "アイウエオ"

    def test_mixed(self):
        """混在の場合"""
        assert normalize_reading("あいウエお") == "アイウエオ"
