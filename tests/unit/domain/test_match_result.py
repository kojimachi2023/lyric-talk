"""
Test module for MatchResult value object and MatchType enum
Tests are written BEFORE implementation (TDD Red phase)
"""

import pytest

from src.domain.models.match_result import (
    MatchResult,
    MatchType,
    MoraMatchDetail,
)


class TestMatchType:
    """MatchType列挙型のテスト"""

    def test_match_type_values(self):
        """MatchTypeが正しい値を持つことを確認"""
        assert MatchType.EXACT_SURFACE == "exact_surface"
        assert MatchType.EXACT_READING == "exact_reading"
        assert MatchType.MORA_COMBINATION == "mora_combination"
        assert MatchType.NO_MATCH == "no_match"

    def test_match_type_enumeration(self):
        """MatchTypeが全ての値を列挙できることを確認"""
        types = list(MatchType)
        assert len(types) == 4
        assert MatchType.EXACT_SURFACE in types
        assert MatchType.EXACT_READING in types
        assert MatchType.MORA_COMBINATION in types
        assert MatchType.NO_MATCH in types


class TestMoraMatchDetail:
    """MoraMatchDetail値オブジェクトのテスト"""

    def test_mora_match_detail_creation(self):
        """MoraMatchDetailを作成できることを確認"""
        detail = MoraMatchDetail(mora="ト", source_token_id="token_001_0_1", mora_index=0)
        assert detail.mora == "ト"
        assert detail.source_token_id == "token_001_0_1"
        assert detail.mora_index == 0

    def test_mora_match_detail_immutability(self):
        """MoraMatchDetailは不変であることを確認"""

        detail = MoraMatchDetail(mora="キョ", source_token_id="token_002_1_2", mora_index=1)
        with pytest.raises((AttributeError, Exception)):
            detail.mora = "ト"


class TestMatchResult:
    """MatchResult値オブジェクトのテスト"""

    def test_match_result_exact_surface(self):
        """表層形完全一致のMatchResultを作成できることを確認"""
        result = MatchResult(
            input_token="東京",
            input_reading="トウキョウ",
            match_type=MatchType.EXACT_SURFACE,
            matched_token_ids=["token_001_0_1"],
            mora_details=None,
        )
        assert result.input_token == "東京"
        assert result.input_reading == "トウキョウ"
        assert result.match_type == MatchType.EXACT_SURFACE
        assert result.matched_token_ids == ["token_001_0_1"]
        assert result.mora_details is None

    def test_match_result_exact_reading(self):
        """読み完全一致のMatchResultを作成できることを確認"""
        result = MatchResult(
            input_token="とうきょう",
            input_reading="トウキョウ",
            match_type=MatchType.EXACT_READING,
            matched_token_ids=["token_002_1_3"],
            mora_details=None,
        )
        assert result.match_type == MatchType.EXACT_READING
        assert result.matched_token_ids == ["token_002_1_3"]

    def test_match_result_mora_combination(self):
        """モーラ組み合わせのMatchResultを作成できることを確認"""
        mora_details = [
            MoraMatchDetail(mora="ト", source_token_id="token_001_0_0", mora_index=0),
            MoraMatchDetail(mora="ウ", source_token_id="token_001_0_1", mora_index=1),
        ]
        result = MatchResult(
            input_token="とう",
            input_reading="トウ",
            match_type=MatchType.MORA_COMBINATION,
            matched_token_ids=["token_001_0_0", "token_001_0_1"],
            mora_details=mora_details,
        )
        assert result.match_type == MatchType.MORA_COMBINATION
        assert len(result.mora_details) == 2
        assert result.mora_details[0].mora == "ト"
        assert result.mora_details[1].mora == "ウ"

    def test_match_result_no_match(self):
        """マッチなしのMatchResultを作成できることを確認"""
        result = MatchResult(
            input_token="存在しない",
            input_reading="ソンザイシナイ",
            match_type=MatchType.NO_MATCH,
            matched_token_ids=[],
            mora_details=None,
        )
        assert result.match_type == MatchType.NO_MATCH
        assert result.matched_token_ids == []
        assert result.mora_details is None

    def test_match_result_immutability(self):
        """値オブジェクトなので不変であることを確認"""
        import pytest

        result = MatchResult(
            input_token="テスト",
            input_reading="テスト",
            match_type=MatchType.EXACT_SURFACE,
            matched_token_ids=["token_001"],
            mora_details=None,
        )
        # 値オブジェクトなので変更できない
        with pytest.raises((AttributeError, Exception)):
            result.input_token = "変更"

    def test_match_result_empty_matched_token_ids_default(self):
        """matched_token_idsがデフォルトで空リストであることを確認"""
        result = MatchResult(
            input_token="テスト",
            input_reading="テスト",
            match_type=MatchType.NO_MATCH,
        )
        assert result.matched_token_ids == []
        assert result.mora_details is None

    def test_match_result_with_multiple_matched_tokens(self):
        """複数のマッチトークンIDを持つMatchResultを作成できることを確認"""
        result = MatchResult(
            input_token="学校",
            input_reading="ガッコウ",
            match_type=MatchType.EXACT_SURFACE,
            matched_token_ids=["token_001_0_5", "token_002_1_3", "token_003_2_1"],
            mora_details=None,
        )
        assert len(result.matched_token_ids) == 3
        assert "token_001_0_5" in result.matched_token_ids
        assert "token_002_1_3" in result.matched_token_ids
        assert "token_003_2_1" in result.matched_token_ids
