"""
テスト共有フィクスチャ設定

すべてのテストファイルで使用できるフィクスチャ（nlp, mock_model, mock_tokenizer）を
一元管理し、transformersモデルの読み込みを効率的にモック化する。
"""

from unittest.mock import Mock

import pytest
import spacy
import torch


@pytest.fixture(scope="session")
def nlp():
    """
    spaCy日本語モデル（セッションスコープ）

    比較的軽量なため実物を使用。テスト全体で1回のみロード。
    """
    return spacy.load("ja_ginza")


@pytest.fixture
def mock_model():
    """
    モックされたBERTモデル

    入力トークン数に応じて動的にhidden_statesの形状を変更。
    torch.manual_seed(42)で決定的な出力を保証し、テストの再現性を確保。
    """

    class MockBERTModel(Mock):
        def __call__(self, **kwargs):
            # 入力トークン数に応じて動的にhidden_statesを生成
            seq_len = kwargs["input_ids"].shape[1]
            hidden_size = 768

            # 固定シードで決定的な出力を生成
            torch.manual_seed(42)

            outputs = Mock()
            # 13層のhidden_statesを生成（embedding layer + 12 transformer layers）
            outputs.hidden_states = tuple(torch.randn(1, seq_len, hidden_size) for _ in range(13))
            return outputs

        def to(self, device=None, dtype=None, **kwargs):
            # device変更: 自分自身を返す（自身が既にモック）
            return self

        def eval(self):
            # eval mode設定: 自分自身を返す
            return self

    model = MockBERTModel()
    model.config = Mock()
    model.config.hidden_size = 768

    return model


@pytest.fixture
def mock_tokenizer():
    """
    モックされたBERTトークナイザー

    テキストをトークナイズし、input_ids と attention_mask を返す。
    convert_ids_to_tokens メソッドも実装。
    """
    tokenizer = Mock()

    def tokenizer_call(text, return_tensors=None, add_special_tokens=True):
        # 簡易的なトークナイゼーション（テスト用）
        # 実際のトークナイザーの代わりに、テキスト長に基づいて動的にトークン数を決定
        tokens = text.split()
        num_tokens = len(tokens) + 2 if add_special_tokens else len(tokens)  # +2: [CLS], [SEP]

        token_ids = list(range(num_tokens))

        result = {
            "input_ids": torch.tensor([token_ids]),
            "attention_mask": torch.ones(1, num_tokens, dtype=torch.long),
        }

        if return_tensors == "pt":
            return result
        return result

    tokenizer.side_effect = tokenizer_call

    def convert_ids_to_tokens_impl(token_ids):
        # token_ids が1次元の場合
        if token_ids.dim() == 1:
            token_ids = token_ids.tolist()
        tokens = ["[CLS]"] + [f"token_{i}" for i in range(len(token_ids) - 2)] + ["[SEP]"]
        return tokens

    tokenizer.convert_ids_to_tokens = Mock(side_effect=convert_ids_to_tokens_impl)

    return tokenizer
