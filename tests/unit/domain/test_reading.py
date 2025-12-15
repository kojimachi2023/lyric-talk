"""
Test module for Reading value object
Tests are written BEFORE implementation (TDD Red phase)
"""

import pytest

from src.domain.models.mora import Mora
from src.domain.models.reading import Reading


class TestReading:
    """Reading値オブジェクトのテスト"""

    def test_reading_creation_with_hiragana(self):
        """ひらがなでReadingを作成"""
        reading = Reading(raw="とうきょう")
        assert reading.raw == "とうきょう"

    def test_reading_creation_with_katakana(self):
        """カタカナでReadingを作成"""
        reading = Reading(raw="トウキョウ")
        assert reading.raw == "トウキョウ"

    def test_reading_normalized_hiragana_to_katakana(self):
        """ひらがなをカタカナに正規化"""
        reading = Reading(raw="とうきょう")
        assert reading.normalized == "トウキョウ"

    def test_reading_normalized_already_katakana(self):
        """すでにカタカナの場合はそのまま"""
        reading = Reading(raw="トウキョウ")
        assert reading.normalized == "トウキョウ"

    def test_reading_normalized_mixed_kana(self):
        """混在した仮名を正規化"""
        reading = Reading(raw="とうキョウ")
        assert reading.normalized == "トウキョウ"

    def test_reading_normalized_empty_string(self):
        """空文字列の正規化"""
        reading = Reading(raw="")
        assert reading.normalized == ""

    def test_reading_to_moras(self):
        """Readingからモーラのリストを取得"""
        reading = Reading(raw="とうきょう")
        moras = reading.to_moras()
        assert isinstance(moras, list)
        assert len(moras) == 4  # ト、ウ、キョ、ウ
        assert all(isinstance(m, Mora) for m in moras)
        assert [m.value for m in moras] == ["ト", "ウ", "キョ", "ウ"]

    def test_reading_to_moras_from_katakana(self):
        """カタカナのReadingからモーラのリストを取得"""
        reading = Reading(raw="ファイティング")
        moras = reading.to_moras()
        assert len(moras) == 5  # ファ、イ、ティ、ン、グ
        assert [m.value for m in moras] == ["ファ", "イ", "ティ", "ン", "グ"]

    def test_reading_to_moras_with_youon(self):
        """拗音を含むReadingのモーラ分割"""
        reading = Reading(raw="きょうと")
        moras = reading.to_moras()
        assert len(moras) == 3  # キョ、ウ、ト
        assert [m.value for m in moras] == ["キョ", "ウ", "ト"]

    def test_reading_to_moras_empty_string(self):
        """空文字列のモーラ分割"""
        reading = Reading(raw="")
        moras = reading.to_moras()
        assert moras == []

    def test_reading_immutability(self):
        """Readingは不変であることを確認"""
        reading = Reading(raw="とうきょう")
        with pytest.raises((AttributeError, Exception)):
            # frozen=TrueのBaseModelは属性変更時にエラーを発生
            reading.raw = "おおさか"

    def test_reading_equality(self):
        """同じ値を持つReadingは等しい"""
        reading1 = Reading(raw="とうきょう")
        reading2 = Reading(raw="とうきょう")
        assert reading1 == reading2

    def test_reading_inequality(self):
        """異なる値を持つReadingは等しくない"""
        reading1 = Reading(raw="とうきょう")
        reading2 = Reading(raw="おおさか")
        assert reading1 != reading2

    def test_reading_hash(self):
        """Readingはハッシュ可能"""
        reading1 = Reading(raw="とうきょう")
        reading2 = Reading(raw="とうきょう")
        # 不変オブジェクトなので同じハッシュを持つべき
        assert hash(reading1) == hash(reading2)
        # セットに追加できることを確認
        reading_set = {reading1, reading2}
        assert len(reading_set) == 1

    def test_reading_normalized_is_computed_property(self):
        """normalizedは計算プロパティであることを確認"""
        reading = Reading(raw="とうきょう")
        # 複数回アクセスしても同じ値
        assert reading.normalized == reading.normalized
        assert reading.normalized == "トウキョウ"
