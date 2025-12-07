"""
トークンアライメントユーティリティ

spaCyトークンとtransformersサブワードトークンをアライメントし、
各spaCyトークンに対応する隠れ状態を抽出する。
"""

from dataclasses import dataclass

import spacy
import torch
from transformers import AutoModel, AutoTokenizer


@dataclass
class AlignedEmbedding:
    """アライメントされた埋め込み"""

    spacy_token_index: int  # spaCyトークンのインデックス
    spacy_token_text: str  # spaCyトークンのテキスト
    embedding: list[float]  # 隠れ状態ベクトル（平均プーリング済み）
    subword_indices: list[int]  # 対応するtransformersサブワードトークンのインデックス


class TokenAligner:
    """
    spaCyトークンとtransformersサブワードトークンのアライメント処理

    文字位置ベースでアライメントを行い、各spaCyトークンに対応する
    transformersの隠れ状態を抽出する。
    """

    def __init__(
        self,
        transformer_model_name: str,
        hidden_layer: int = -1,
        pooling_strategy: str = "mean",
    ):
        """
        Args:
            transformer_model_name: transformersモデル名
            hidden_layer: 隠れ状態を抽出するレイヤー（-1は最終層）
            pooling_strategy: プーリング方式（"mean", "first", "last"）
        """
        self.tokenizer = AutoTokenizer.from_pretrained(transformer_model_name)
        self.model = AutoModel.from_pretrained(
            transformer_model_name,
            output_hidden_states=True,  # 隠れ状態を出力
        )
        self.hidden_layer = hidden_layer
        self.pooling_strategy = pooling_strategy

        # 評価モードに設定
        self.model.eval()

    def align_and_extract(
        self,
        text: str,
        spacy_doc: spacy.tokens.Doc,
    ) -> list[AlignedEmbedding]:
        """
        spaCyトークンとtransformersサブワードトークンをアライメントし、
        各spaCyトークンの隠れ状態を抽出する。

        Args:
            text: 入力テキスト
            spacy_doc: spaCyで処理済みのDoc

        Returns:
            各spaCyトークンのアライメント済み埋め込みのリスト
        """
        # transformersでトークナイズ
        encoded = self.tokenizer(
            text,
            return_tensors="pt",
            add_special_tokens=True,
        )

        # 隠れ状態を取得
        with torch.no_grad():
            outputs = self.model(**encoded)
            hidden_states = outputs.hidden_states[self.hidden_layer]  # (batch, seq_len, hidden_dim)

        # バッチサイズ1を前提
        hidden_states = hidden_states.squeeze(0)  # (seq_len, hidden_dim)

        # トークンとオフセットマッピングを手動で計算
        tokens = self.tokenizer.convert_ids_to_tokens(encoded["input_ids"].squeeze(0))
        offset_mapping = self._compute_offset_mapping(text, tokens)

        # 各spaCyトークンをアライメント
        aligned_embeddings = []
        for spacy_token in spacy_doc:
            # 空白・記号はスキップ
            if spacy_token.is_space or spacy_token.is_punct:
                continue

            # spaCyトークンの文字位置
            spacy_start = spacy_token.idx
            spacy_end = spacy_token.idx + len(spacy_token.text)

            # 対応するtransformersサブワードトークンのインデックスを取得
            subword_indices = self._find_overlapping_subwords(spacy_start, spacy_end, offset_mapping)

            if not subword_indices:
                # マッチするサブワードがない場合はスキップ
                # （通常は発生しないが、安全のため）
                continue

            # 対応する隠れ状態を抽出してプーリング
            subword_hidden_states = hidden_states[subword_indices]  # (n_subwords, hidden_dim)
            pooled_embedding = self._pool_hidden_states(subword_hidden_states)

            aligned_embeddings.append(
                AlignedEmbedding(
                    spacy_token_index=spacy_token.i,
                    spacy_token_text=spacy_token.text,
                    embedding=pooled_embedding.tolist(),
                    subword_indices=subword_indices,
                )
            )

        return aligned_embeddings

    def _find_overlapping_subwords(
        self,
        spacy_start: int,
        spacy_end: int,
        offset_mapping: list[tuple[int, int]],
    ) -> list[int]:
        """
        spaCyトークンの文字位置と重なるtransformersサブワードトークンのインデックスを取得

        Args:
            spacy_start: spaCyトークンの開始位置
            spacy_end: spaCyトークンの終了位置
            offset_mapping: transformersのoffset_mapping リスト

        Returns:
            重なるサブワードトークンのインデックスリスト
        """
        overlapping_indices = []

        for idx, (start, end) in enumerate(offset_mapping):
            start_pos = start
            end_pos = end

            # 特殊トークン（[CLS], [SEP]など）はスキップ
            if start_pos == 0 and end_pos == 0:
                continue

            # 重なり判定: spaCyトークンとサブワードが少しでも重なっていればOK
            if self._has_overlap(spacy_start, spacy_end, start_pos, end_pos):
                overlapping_indices.append(idx)

        return overlapping_indices

    @staticmethod
    def _has_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
        """2つの区間が重なっているか判定"""
        return not (end1 <= start2 or end2 <= start1)

    def _compute_offset_mapping(
        self,
        text: str,
        tokens: list[str],
    ) -> list[tuple[int, int]]:
        """
        トークンのオフセットマッピングを計算する

        Args:
            text: 元のテキスト
            tokens: トークナイズされたトークンリスト

        Returns:
            各トークンの(start, end)位置のリスト
        """
        offset_mapping = []
        current_pos = 0

        for token in tokens:
            # 特殊トークン（[CLS], [SEP], [PAD]など）
            if token.startswith("[") and token.endswith("]"):
                offset_mapping.append((0, 0))
                continue

            # サブワードプレフィックス（##）を除去
            token_text = token.replace("##", "")

            # トークンテキストが空の場合
            if not token_text:
                offset_mapping.append((current_pos, current_pos))
                continue

            # テキスト内でトークンを検索
            # 空白を飛ばす
            while current_pos < len(text) and text[current_pos].isspace():
                current_pos += 1

            start = current_pos
            # トークンテキストを探す
            found = False
            for i in range(current_pos, len(text)):
                # 空白を無視してマッチング
                text_without_spaces = text[current_pos : i + 1].replace(" ", "")
                if token_text == text_without_spaces:
                    end = i + 1
                    offset_mapping.append((start, end))
                    current_pos = end
                    found = True
                    break

            if not found:
                # マッチしない場合は現在位置を使用
                offset_mapping.append((current_pos, current_pos + len(token_text)))
                current_pos += len(token_text)

        return offset_mapping

    def _pool_hidden_states(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        複数のサブワードの隠れ状態をプーリングする

        Args:
            hidden_states: (n_subwords, hidden_dim)

        Returns:
            プーリング済みの隠れ状態 (hidden_dim,)
        """
        if self.pooling_strategy == "mean":
            return hidden_states.mean(dim=0)
        elif self.pooling_strategy == "first":
            return hidden_states[0]
        elif self.pooling_strategy == "last":
            return hidden_states[-1]
        else:
            raise ValueError(f"Unknown pooling strategy: {self.pooling_strategy}")
