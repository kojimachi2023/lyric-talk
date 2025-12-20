"""
Test module for LyricsCorpus entity
Tests are written BEFORE implementation (TDD Red phase)
"""

from datetime import datetime

from src.domain.models.lyrics_corpus import LyricsCorpus


class TestLyricsCorpus:
    """LyricsCorpusエンティティのテスト"""

    def test_lyrics_corpus_creation(self):
        """LyricsCorpusを作成できることを確認"""
        now = datetime.now()
        corpus = LyricsCorpus(
            lyrics_corpus_id="test_corpus_001",
            content_hash="abc123def456",
            title="テスト歌詞",
            created_at=now,
        )
        assert corpus.lyrics_corpus_id == "test_corpus_001"
        assert corpus.content_hash == "abc123def456"
        assert corpus.title == "テスト歌詞"
        assert corpus.created_at == now

    def test_lyrics_corpus_without_title(self):
        """タイトルなしでLyricsCorpusを作成できることを確認"""
        now = datetime.now()
        corpus = LyricsCorpus(
            lyrics_corpus_id="test_corpus_002",
            content_hash="hash_value",
            title=None,
            created_at=now,
        )
        assert corpus.lyrics_corpus_id == "test_corpus_002"
        assert corpus.content_hash == "hash_value"
        assert corpus.title is None
        assert corpus.created_at == now

    def test_lyrics_corpus_mutability(self):
        """LyricsCorpusはエンティティなので可変であることを確認"""
        now = datetime.now()
        corpus = LyricsCorpus(
            lyrics_corpus_id="test_corpus_003",
            content_hash="original_hash",
            title="元のタイトル",
            created_at=now,
        )
        # エンティティは可変なので属性を変更できる
        corpus.title = "新しいタイトル"
        assert corpus.title == "新しいタイトル"

    def test_lyrics_corpus_with_uuid(self):
        """UUID形式のIDでLyricsCorpusを作成できることを確認"""
        import uuid

        corpus_id = str(uuid.uuid4())
        now = datetime.now()
        corpus = LyricsCorpus(
            lyrics_corpus_id=corpus_id,
            content_hash="hash123",
            title="UUIDテスト",
            created_at=now,
        )
        assert corpus.lyrics_corpus_id == corpus_id
        # UUIDフォーマットであることを確認
        uuid.UUID(corpus.lyrics_corpus_id)  # 例外が発生しなければOK
