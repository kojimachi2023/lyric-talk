"""
Test module for Mora value object
Tests are written BEFORE implementation (TDD Red phase)
"""

import pytest

from src.domain.models.mora import Mora


class TestMora:
    """Mora値オブジェクトのテスト"""

    def test_mora_creation_with_single_character(self):
        """単一文字でMoraを作成"""
        mora = Mora(value="ト")
        assert mora.value == "ト"

    def test_mora_creation_with_youon(self):
        """拗音（キャ、シュ、チョ等）でMoraを作成"""
        mora = Mora(value="キョ")
        assert mora.value == "キョ"

    def test_mora_creation_with_sokuon(self):
        """促音（ッ）でMoraを作成"""
        mora = Mora(value="ッ")
        assert mora.value == "ッ"

    def test_mora_creation_with_long_vowel(self):
        """長音（ー）でMoraを作成"""
        mora = Mora(value="ー")
        assert mora.value == "ー"

    def test_mora_immutability(self):
        """Moraは不変であることを確認"""
        mora = Mora(value="ト")
        with pytest.raises((AttributeError, Exception)):
            # frozen=TrueのBaseModelは属性変更時にエラーを発生
            mora.value = "カ"

    def test_mora_split_simple_katakana(self):
        """単純なカタカナをモーラに分割"""
        result = Mora.split("トウキョウ")
        assert len(result) == 4
        assert [m.value for m in result] == ["ト", "ウ", "キョ", "ウ"]

    def test_mora_split_with_sokuon(self):
        """促音を含むカタカナをモーラに分割"""
        result = Mora.split("ガッコウ")
        expected_values = ["ガ", "ッ", "コ", "ウ"]
        assert len(result) == 4
        assert [m.value for m in result] == expected_values

    def test_mora_split_with_long_vowel(self):
        """長音を含むカタカナをモーラに分割"""
        result = Mora.split("キャー")
        expected_values = ["キャ", "ー"]
        assert len(result) == 2
        assert [m.value for m in result] == expected_values

    def test_mora_split_with_small_vowels(self):
        """小さいァィゥェォを含むカタカナをモーラに分割"""
        result = Mora.split("ファイティング")
        expected_values = ["ファ", "イ", "ティ", "ン", "グ"]
        assert len(result) == 5
        assert [m.value for m in result] == expected_values

    def test_mora_split_empty_string(self):
        """空文字列のモーラ分割"""
        result = Mora.split("")
        assert result == []

    def test_mora_split_single_character(self):
        """単一文字のモーラ分割"""
        result = Mora.split("ト")
        assert len(result) == 1
        assert result[0].value == "ト"

    def test_mora_split_with_multiple_youon(self):
        """複数の拗音を含むカタカナをモーラに分割"""
        result = Mora.split("キョウト")
        expected_values = ["キョ", "ウ", "ト"]
        assert len(result) == 3
        assert [m.value for m in result] == expected_values

    def test_mora_equality(self):
        """同じ値を持つMoraは等しい"""
        mora1 = Mora(value="ト")
        mora2 = Mora(value="ト")
        assert mora1 == mora2

    def test_mora_inequality(self):
        """異なる値を持つMoraは等しくない"""
        mora1 = Mora(value="ト")
        mora2 = Mora(value="カ")
        assert mora1 != mora2

    def test_mora_hash(self):
        """Moraはハッシュ可能"""
        mora1 = Mora(value="ト")
        mora2 = Mora(value="ト")
        # 不変オブジェクトなので同じハッシュを持つべき
        assert hash(mora1) == hash(mora2)
        # セットに追加できることを確認
        mora_set = {mora1, mora2}
        assert len(mora_set) == 1
