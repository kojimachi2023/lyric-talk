"""
トークンアライメントのテストケース
"""

from unittest.mock import patch

import pytest
import torch

from src.token_alignment import AlignedEmbedding, TokenAligner


@pytest.fixture
def aligner(mock_model):
    """TokenAlignerインスタンス（モデルをモック化）"""
    # AutoModel.from_pretrainedのみをモック化
    # AutoTokenizerは軽量なのでそのまま使用
    with patch("src.token_alignment.AutoModel.from_pretrained", return_value=mock_model):
        return TokenAligner(
            transformer_model_name="cl-tohoku/bert-base-japanese-v3",
            hidden_layer=-1,
            pooling_strategy="mean",
        )


class TestTokenAligner:
    """TokenAlignerのテスト"""

    def test_simple_sentence(self, nlp, aligner):
        """シンプルな文のアライメント"""
        text = "今日は良い天気です"
        doc = nlp(text)

        aligned = aligner.align_and_extract(text, doc)

        # 空白・記号を除いたトークン数と一致するはず
        non_punct_tokens = [t for t in doc if not t.is_space and not t.is_punct]
        assert len(aligned) == len(non_punct_tokens)

        # 各アライメント結果の検証
        for emb in aligned:
            assert isinstance(emb, AlignedEmbedding)
            assert isinstance(emb.spacy_token_index, int)
            assert isinstance(emb.spacy_token_text, str)
            assert isinstance(emb.embedding, list)
            assert isinstance(emb.subword_indices, list)
            assert len(emb.embedding) > 0  # 埋め込みベクトルが存在
            assert len(emb.subword_indices) > 0  # 少なくとも1つのサブワードに対応

    def test_token_text_matches(self, nlp, aligner):
        """トークンテキストが正しく保持されているか"""
        text = "猫が好きです"
        doc = nlp(text)

        aligned = aligner.align_and_extract(text, doc)

        # トークンテキストの検証
        expected_tokens = [t.text for t in doc if not t.is_space and not t.is_punct]
        actual_tokens = [emb.spacy_token_text for emb in aligned]

        assert actual_tokens == expected_tokens

    def test_embedding_dimension(self, nlp, aligner):
        """埋め込みベクトルの次元数が正しいか"""
        # BERT-base-japaneseの隠れ状態次元は768
        expected_dim = aligner.model.config.hidden_size

        text = "テスト文章"
        doc = nlp(text)

        aligned = aligner.align_and_extract(text, doc)

        for emb in aligned:
            assert len(emb.embedding) == expected_dim

    def test_subword_overlap(self, nlp, aligner):
        """
        サブワードの重なり判定テスト

        transformersのtokenizerは単語を複数のサブワードに分割することがあるため、
        各spaCyトークンが少なくとも1つのサブワードにマッチすることを確認
        """
        text = "プログラミング"  # 長い単語（複数サブワードに分割される可能性）
        doc = nlp(text)

        aligned = aligner.align_and_extract(text, doc)

        assert len(aligned) > 0
        for emb in aligned:
            # 少なくとも1つのサブワードにマッチしているはず
            assert len(emb.subword_indices) >= 1

    def test_pooling_strategies(self, nlp, mock_model):
        """プーリング戦略の違いを検証"""
        text = "今日は晴れです"
        doc = nlp(text)

        # 異なるプーリング戦略でアライメント（モデルをモック化）
        with patch("src.token_alignment.AutoModel.from_pretrained", return_value=mock_model):
            aligner_mean = TokenAligner(
                transformer_model_name="cl-tohoku/bert-base-japanese-v3",
                pooling_strategy="mean",
            )
            aligner_first = TokenAligner(
                transformer_model_name="cl-tohoku/bert-base-japanese-v3",
                pooling_strategy="first",
            )
            aligner_last = TokenAligner(
                transformer_model_name="cl-tohoku/bert-base-japanese-v3",
                pooling_strategy="last",
            )

            aligned_mean = aligner_mean.align_and_extract(text, doc)
            aligned_first = aligner_first.align_and_extract(text, doc)
            aligned_last = aligner_last.align_and_extract(text, doc)

        # トークン数は同じはず
        assert len(aligned_mean) == len(aligned_first) == len(aligned_last)

        # 埋め込みベクトルは異なるはず（複数サブワードを持つトークンがあれば）
        # ただし、単一サブワードのトークンは同じになる可能性がある
        for mean_emb, first_emb, last_emb in zip(aligned_mean, aligned_first, aligned_last):
            assert len(mean_emb.embedding) == len(first_emb.embedding) == len(last_emb.embedding)

    def test_empty_text(self, nlp, aligner):
        """空文字列のテスト"""
        text = ""
        doc = nlp(text)

        aligned = aligner.align_and_extract(text, doc)

        assert len(aligned) == 0

    def test_punctuation_only(self, nlp, aligner):
        """記号のみの文のテスト"""
        text = "。、！？"
        doc = nlp(text)

        aligned = aligner.align_and_extract(text, doc)

        # 記号はスキップされるため、空のリストが返るはず
        assert len(aligned) == 0

    def test_has_overlap(self):
        """区間の重なり判定メソッドのテスト"""
        # 完全に重なる
        assert TokenAligner._has_overlap(0, 5, 2, 4) is True

        # 部分的に重なる
        assert TokenAligner._has_overlap(0, 5, 3, 8) is True
        assert TokenAligner._has_overlap(3, 8, 0, 5) is True

        # 境界で接する（重ならない）
        assert TokenAligner._has_overlap(0, 5, 5, 10) is False

        # 完全に離れている
        assert TokenAligner._has_overlap(0, 5, 10, 15) is False

        # 完全に包含
        assert TokenAligner._has_overlap(0, 10, 2, 8) is True
        assert TokenAligner._has_overlap(2, 8, 0, 10) is True

    def test_alignment_consistency(self, nlp, aligner):
        """
        同じ文を複数回処理した場合、同じ結果が得られるか
        （非決定性のバグがないことを確認）
        """
        text = "美しい朝の光"
        doc = nlp(text)

        aligned1 = aligner.align_and_extract(text, doc)
        aligned2 = aligner.align_and_extract(text, doc)

        assert len(aligned1) == len(aligned2)

        for emb1, emb2 in zip(aligned1, aligned2):
            assert emb1.spacy_token_index == emb2.spacy_token_index
            assert emb1.spacy_token_text == emb2.spacy_token_text
            assert emb1.subword_indices == emb2.subword_indices
            # 埋め込みベクトルも一致するはず（浮動小数点誤差を考慮）
            assert torch.allclose(
                torch.tensor(emb1.embedding),
                torch.tensor(emb2.embedding),
                rtol=1e-5,
            )

    def test_complex_sentence_with_kanji(self, nlp, aligner):
        """漢字を含む複雑な文のテスト"""
        text = "人工知能の研究開発は急速に進展しています"
        doc = nlp(text)

        aligned = aligner.align_and_extract(text, doc)

        # 空白・記号を除いたトークン数と一致
        non_punct_tokens = [t for t in doc if not t.is_space and not t.is_punct]
        assert len(aligned) == len(non_punct_tokens)

        # 全てのトークンが埋め込みを持つ
        for emb in aligned:
            assert len(emb.embedding) > 0
            assert len(emb.subword_indices) > 0
