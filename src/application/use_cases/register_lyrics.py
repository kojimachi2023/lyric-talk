"""RegisterLyricsUseCase implementation."""

import hashlib
import uuid
from datetime import datetime

from src.domain.models.lyric_token import LyricToken
from src.domain.models.lyrics_corpus import LyricsCorpus
from src.domain.models.reading import Reading
from src.domain.repositories.lyric_token_repository import LyricTokenRepository
from src.domain.repositories.lyrics_repository import LyricsRepository
from src.domain.services.nlp_service import NlpService


class RegisterLyricsUseCase:
    """Use case for registering lyrics."""

    def __init__(
        self,
        nlp_service: NlpService,
        lyrics_repository: LyricsRepository,
        lyric_token_repository: LyricTokenRepository,
    ):
        self.nlp_service = nlp_service
        self.lyrics_repository = lyrics_repository
        self.lyric_token_repository = lyric_token_repository

    def execute(self, lyrics_text: str, artist=None, title=None) -> str:
        """Register lyrics and return corpus_id.

        Args:
            lyrics_text: Lyrics text to register
            artist: (Optional) Artist name
            title: (Optional) Song title

        Returns:
            corpus_id: ID of the registered or existing corpus
        """
        # Calculate content hash
        content_hash = hashlib.sha256(lyrics_text.encode("utf-8")).hexdigest()

        # Check if corpus already exists
        existing_corpus = self.lyrics_repository.find_by_content_hash(content_hash)
        if existing_corpus:
            return existing_corpus.lyrics_corpus_id

        # Tokenize lyrics
        token_data_list = self.nlp_service.tokenize(lyrics_text)

        # Generate corpus_id

        corpus_id = f"corpus_{uuid.uuid4().hex[:12]}"

        # Create LyricsCorpus entity
        corpus = LyricsCorpus(
            lyrics_corpus_id=corpus_id,
            content_hash=content_hash,
            created_at=datetime.now(),
            artist=artist,
            title=title,
        )

        # Save corpus
        saved_corpus_id = self.lyrics_repository.save(corpus)

        # Create LyricToken entities
        tokens = []
        for idx, token_data in enumerate(token_data_list):
            token = LyricToken(
                lyrics_corpus_id=saved_corpus_id,
                surface=token_data.surface,
                reading=Reading(raw=token_data.reading),
                lemma=token_data.lemma,
                pos=token_data.pos,
                line_index=0,  # TODO: line_index should be extracted from tokenization
                token_index=idx,
            )
            tokens.append(token)

        # Save tokens
        self.lyric_token_repository.save_batch(tokens)

        return saved_corpus_id
