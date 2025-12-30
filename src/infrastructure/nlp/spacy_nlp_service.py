"""SpaCy + GiNZA implementation of NlpService."""

from typing import List

import spacy
from spacy.tokens import Doc

from src.application.dtos.token_data import TokenData
from src.domain.services.nlp_service import NlpService


class SpacyNlpService(NlpService):
    """SpaCy + GiNZA implementation of NlpService.

    Uses Japanese language model (ja_ginza) for tokenization and morphological analysis.
    """

    def __init__(self, model_name: str = "ja_ginza"):
        """Initialize SpaCy NLP service.

        Args:
            model_name: SpaCy model name (default: ja_ginza)
        """
        self.nlp = spacy.load(
            model_name,
            disable=[
                "parser",  # Not used (syntax parsing)
                "ner",  # Not used (named entity recognition)
                "tok2vec",  # Not used (token vectors)
                "compound_splitter",  # Not used (compound word splitting)
                "bunsetu_recognizer",  # Not used (phrase boundary detection)
            ],
        )

    def tokenize(self, text: str) -> List[TokenData]:
        """Tokenize text using SpaCy + GiNZA.

        Args:
            text: Text to tokenize

        Returns:
            List of TokenData objects
        """
        if not text or not text.strip():
            return []

        doc: Doc = self.nlp(text)

        tokens = []
        for token in doc:
            # Skip whitespace-only tokens
            if token.is_space:
                continue

            # Get reading from token attributes
            # GiNZA provides reading in the `reading` extension
            reading = self._get_reading(token)

            token_data = TokenData(
                surface=token.text,
                reading=reading,
                lemma=token.lemma_,
                pos=token.pos_,
            )
            tokens.append(token_data)

        return tokens

    def _get_reading(self, token) -> str:
        """Get reading (katakana) from token.

        Args:
            token: SpaCy token

        Returns:
            Reading in katakana (fallback to surface if not available)
        """
        # Try to get from morph features first (GiNZA stores reading here)
        morph_dict = token.morph.to_dict()
        if "Reading" in morph_dict:
            return morph_dict["Reading"]

        # Try custom extension if available
        try:
            if hasattr(token._, "reading") and token._.reading:
                return token._.reading
        except (AttributeError, KeyError):
            pass

        # Last resort: use the surface form
        return token.text
