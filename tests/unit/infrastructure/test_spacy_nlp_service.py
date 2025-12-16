"""Tests for SpaCy NlpService implementation."""

import pytest

from src.infrastructure.nlp.spacy_nlp_service import SpacyNlpService


@pytest.mark.slow
def test_spacy_nlp_service_tokenize():
    """Test SpaCyNlpService tokenize method with simple Japanese text."""
    # Import will fail initially (Red phase)

    service = SpacyNlpService()

    # Test simple Japanese text
    text = "東京へ行く"
    tokens = service.tokenize(text)

    # Verify tokens are returned
    assert len(tokens) > 0

    # Verify TokenData structure
    for token in tokens:
        assert hasattr(token, "surface")
        assert hasattr(token, "reading")
        assert hasattr(token, "lemma")
        assert hasattr(token, "pos")
        assert isinstance(token.surface, str)
        assert isinstance(token.reading, str)


@pytest.mark.slow
def test_spacy_nlp_service_reading_extraction():
    """Test that readings are properly extracted."""

    service = SpacyNlpService()

    text = "東京"
    tokens = service.tokenize(text)

    # Should have at least one token
    assert len(tokens) >= 1

    # First token should have a reading
    # GiNZA typically provides katakana readings
    assert len(tokens[0].reading) > 0


@pytest.mark.slow
def test_spacy_nlp_service_empty_text():
    """Test SpaCyNlpService with empty text."""

    service = SpacyNlpService()

    # Empty text should return empty list
    tokens = service.tokenize("")
    assert len(tokens) == 0


@pytest.mark.slow
def test_spacy_nlp_service_whitespace_only():
    """Test SpaCyNlpService with whitespace-only text."""

    service = SpacyNlpService()

    # Whitespace-only text should return empty or only whitespace tokens
    tokens = service.tokenize("   ")
    # Either empty or whitespace tokens (depends on spaCy config)
    assert isinstance(tokens, list)


@pytest.mark.slow
def test_spacy_nlp_service_multiple_sentences():
    """Test SpaCyNlpService with multiple sentences."""

    service = SpacyNlpService()

    text = "こんにちは。元気ですか。"
    tokens = service.tokenize(text)

    # Should have multiple tokens
    assert len(tokens) > 2

    # Each token should have valid data
    for token in tokens:
        assert len(token.surface) > 0
