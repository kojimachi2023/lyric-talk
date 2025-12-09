"""
テスト共有フィクスチャ設定

すべてのテストファイルで使用できるフィクスチャ（nlp）を一元管理する。
"""

import pytest
import spacy


@pytest.fixture(scope="session")
def nlp():
    """
    spaCy日本語モデル（セッションスコープ）

    比較的軽量なため実物を使用。テスト全体で1回のみロード。
    """
    return spacy.load("ja_ginza")
