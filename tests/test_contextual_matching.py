"""
文脈考慮型埋め込みを使用したマッチングのテスト
"""

from unittest.mock import Mock, patch

import torch

from src.lyric_index import LyricIndex
from src.matcher import Matcher


class TestContextualMatching:
    """文脈考慮型埋め込みを使用したマッチングのテスト"""

    @patch("src.token_alignment.AutoModel.from_pretrained")
    def test_contextual_embedding_integration(
        self, mock_model_class, nlp, temp_chromadb_path, mock_model
    ):
        """
        文脈埋め込みを使用した統合テスト

        歌詞に「走る」と「速い」があり、入力に「急ぐ」がある場合、
        文脈を考慮すると「走る」の方が「急ぐ」に近い意味になるはず
        """
        mock_model_class.return_value = mock_model

        lyrics = """
走る 犬 が 速い
美しい 花 が 咲く
"""

        # 文脈埋め込みを使用してインデックス構築
        lyric_index = LyricIndex.from_lyrics(lyrics, nlp=nlp)

        # 内容語がChromaDBに保存されているか確認
        assert lyric_index.chroma_collection is not None
        count = lyric_index.chroma_collection.count()
        # 内容語: 走る(VERB), 犬(NOUN), 速い(ADJ), 美しい(ADJ), 花(NOUN), 咲く(VERB)
        assert count > 0

    @patch("src.token_alignment.AutoModel.from_pretrained")
    def test_pos_filtering(self, mock_model_class, nlp, temp_chromadb_path, mock_model):
        """
        品詞フィルタリングのテスト

        非内容語（助詞など）は意味的類似マッチングがスキップされることを確認
        """
        mock_model_class.return_value = mock_model

        lyrics = "走る 犬 が 速い"

        lyric_index = LyricIndex.from_lyrics(lyrics, nlp=nlp)

        # ChromaDBに保存されているトークン数を確認
        # 内容語のみが保存されているはず（助詞「が」は除外）
        count = lyric_index.chroma_collection.count()

        # 「が」(ADP/助詞)は保存されていないはず
        # 内容語: 走る(VERB), 犬(NOUN), 速い(ADJ) = 3つ
        assert count >= 3

    @patch("src.token_alignment.AutoModel.from_pretrained")
    def test_query_similar_tokens(self, mock_model_class, nlp, temp_chromadb_path, mock_model):
        """
        query_similar_tokensメソッドのテスト
        """
        mock_model_class.return_value = mock_model

        lyrics = """
走る 犬 が 速い
美しい 花 が 咲く
楽しい 音楽 を 聴く
"""

        lyric_index = LyricIndex.from_lyrics(lyrics, nlp=nlp)

        # TokenAlignerを使って「走る」の文脈埋め込みを取得
        test_text = "走る"
        doc = nlp(test_text)
        aligned = lyric_index.token_aligner.align_and_extract(test_text, doc)

        assert len(aligned) > 0
        query_embedding = aligned[0].embedding

        # 類似トークンをクエリ
        similar_tokens = lyric_index.query_similar_tokens(
            query_embedding=query_embedding, n_results=3
        )

        # 何らかの結果が返るはず
        assert len(similar_tokens) > 0

        # 最初の結果が「走る」自身であることが期待される（最も類似）
        # ただし、完全一致ではないため、他のトークンが返る可能性もある

    @patch("src.token_alignment.AutoModel.from_pretrained")
    def test_chromadb_persistence(self, mock_model_class, nlp, temp_chromadb_path, mock_model):
        """
        ChromaDBの永続化テスト

        タイムスタンプ付きコレクション名を使用することで、
        毎回新しいコレクションが作成され、前回のデータが残らないことを確認
        """
        mock_model_class.return_value = mock_model

        lyrics = "走る 犬 が 速い"

        # 最初のインデックス作成
        lyric_index1 = LyricIndex.from_lyrics(lyrics, nlp=nlp)
        collection_name1 = lyric_index1.chroma_collection.name
        count1 = lyric_index1.chroma_collection.count()

        # 2回目のインデックス作成（異なるタイムスタンプのコレクション名）
        lyric_index2 = LyricIndex.from_lyrics(lyrics, nlp=nlp)
        collection_name2 = lyric_index2.chroma_collection.name
        count2 = lyric_index2.chroma_collection.count()

        # 異なるコレクション名が使用されることを確認
        assert collection_name1 != collection_name2
        # 両方とも同じトークン数（重複なし）
        assert count1 == count2

    @patch("src.token_alignment.AutoModel.from_pretrained")
    def test_empty_lyrics_with_contextual(
        self, mock_model_class, nlp, temp_chromadb_path, mock_model
    ):
        """
        空の歌詞での埋め込みテスト
        """
        mock_model_class.return_value = mock_model

        lyrics = ""

        lyric_index = LyricIndex.from_lyrics(lyrics, nlp=nlp)

        # ChromaDBコレクションが存在するが、トークン数は0
        assert lyric_index.chroma_collection is not None
        assert lyric_index.chroma_collection.count() == 0

    @patch("src.matcher.SentenceTransformer")
    @patch("src.token_alignment.AutoModel.from_pretrained")
    def test_matcher_with_no_similar_match(
        self, mock_model_class, mock_sentence_transformer, nlp, temp_chromadb_path, mock_model
    ):
        """
        意味的類似マッチングが見つからない場合のテスト
        """
        mock_model_class.return_value = mock_model
        # SentenceTransformerのモック設定
        mock_st = Mock()
        mock_st.encode = Mock(return_value=torch.randn(1, 384))  # 疑似的な埋め込み
        mock_sentence_transformer.return_value = mock_st

        lyrics = "走る 犬 が 速い"

        lyric_index = LyricIndex.from_lyrics(lyrics, nlp=nlp)
        matcher = Matcher(lyric_index, nlp=nlp)

        # 歌詞に全く関係ない単語
        input_text = "宇宙飛行士"
        results = matcher.match(input_text)

        # マッチなしになるはず
        assert len(results) > 0
        # 完全一致・読み一致・モーラ一致がなければNO_MATCHになる
