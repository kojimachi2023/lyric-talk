"""
Test module for MatchRun entity
Tests are written BEFORE implementation (TDD Red phase)
"""

from datetime import datetime

from src.domain.models.match_run import MatchRun


class TestMatchRun:
    """MatchRunエンティティのテスト"""

    def test_match_run_creation(self):
        """MatchRunを作成できることを確認"""
        now = datetime.now()
        config = {"max_mora_length": 5, "min_confidence": 0.8}
        match_run = MatchRun(
            run_id="run_001",
            lyrics_corpus_id="corpus_001",
            timestamp=now,
            input_text="テスト入力",
            config=config,
        )
        assert match_run.run_id == "run_001"
        assert match_run.lyrics_corpus_id == "corpus_001"
        assert match_run.timestamp == now
        assert match_run.input_text == "テスト入力"
        assert match_run.config == config

    def test_match_run_with_empty_config(self):
        """空の設定でMatchRunを作成できることを確認"""
        now = datetime.now()
        match_run = MatchRun(
            run_id="run_002",
            lyrics_corpus_id="corpus_002",
            timestamp=now,
            input_text="空設定テスト",
            config={},
        )
        assert match_run.run_id == "run_002"
        assert match_run.config == {}

    def test_match_run_mutability(self):
        """MatchRunはエンティティなので可変であることを確認"""
        now = datetime.now()
        match_run = MatchRun(
            run_id="run_003",
            lyrics_corpus_id="corpus_003",
            timestamp=now,
            input_text="元の入力",
            config={"key": "value"},
        )
        # エンティティは可変なので属性を変更できる
        match_run.input_text = "新しい入力"
        assert match_run.input_text == "新しい入力"

    def test_match_run_with_complex_config(self):
        """複雑な設定でMatchRunを作成できることを確認"""
        now = datetime.now()
        complex_config = {
            "max_mora_length": 5,
            "min_confidence": 0.8,
            "strategies": ["exact_surface", "exact_reading", "mora_combination"],
            "metadata": {"version": "1.0", "user": "test"},
        }
        match_run = MatchRun(
            run_id="run_004",
            lyrics_corpus_id="corpus_004",
            timestamp=now,
            input_text="複雑設定テスト",
            config=complex_config,
        )
        assert match_run.config == complex_config
        assert match_run.config["strategies"] == [
            "exact_surface",
            "exact_reading",
            "mora_combination",
        ]
        assert match_run.config["metadata"]["version"] == "1.0"

    def test_match_run_with_uuid(self):
        """UUID形式のIDでMatchRunを作成できることを確認"""
        import uuid

        run_id = str(uuid.uuid4())
        now = datetime.now()
        match_run = MatchRun(
            run_id=run_id,
            lyrics_corpus_id="corpus_005",
            timestamp=now,
            input_text="UUIDテスト",
            config={},
        )
        assert match_run.run_id == run_id
        # UUIDフォーマットであることを確認
        uuid.UUID(match_run.run_id)  # 例外が発生しなければOK

    def test_match_run_with_empty_results(self):
        """MatchRunを空のresultsで作成できることを確認"""
        now = datetime.now()
        match_run = MatchRun(
            run_id="run_006",
            lyrics_corpus_id="corpus_006",
            timestamp=now,
            input_text="空results",
            config={},
            results=[],
        )
        assert match_run.results == []

    def test_match_run_default_results(self):
        """resultsフィールドがデフォルトで空リストであることを確認"""
        now = datetime.now()
        match_run = MatchRun(
            run_id="run_007",
            lyrics_corpus_id="corpus_007",
            timestamp=now,
            input_text="デフォルトresults",
            config={},
        )
        assert match_run.results == []

    def test_match_run_add_result(self):
        """add_result()でMatchResultを追加できることを確認"""
        from unittest.mock import Mock

        now = datetime.now()
        match_run = MatchRun(
            run_id="run_008",
            lyrics_corpus_id="corpus_008",
            timestamp=now,
            input_text="result追加テスト",
            config={},
        )

        # Mock MatchResult
        mock_result = Mock()
        mock_result.input_token = "テスト"

        match_run.add_result(mock_result)

        assert len(match_run.results) == 1
        assert match_run.results[0] == mock_result
