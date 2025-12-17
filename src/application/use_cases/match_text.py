"""MatchTextUseCase implementation."""

import uuid
from datetime import datetime

from src.domain.models.match_result import MatchResult
from src.domain.models.match_run import MatchRun
from src.domain.models.reading import Reading
from src.domain.repositories.match_repository import MatchRepository
from src.domain.services.matching_strategy import MatchingStrategy
from src.domain.services.nlp_service import NlpService


class MatchTextUseCase:
    """Use case for matching text against lyrics."""

    def __init__(
        self,
        nlp_service: NlpService,
        matching_strategy: MatchingStrategy,
        match_repository: MatchRepository,
    ):
        self.nlp_service = nlp_service
        self.matching_strategy = matching_strategy
        self.match_repository = match_repository

    def execute(self, input_text: str) -> str:
        """Match input text against lyrics and return run_id.

        Args:
            input_text: Input text to match

        Returns:
            run_id: ID of the match run
        """
        # Tokenize input text
        token_data_list = self.nlp_service.tokenize(input_text)

        # Generate run_id
        run_id = f"run_{uuid.uuid4().hex[:12]}"

        # Create MatchRun entity (aggregate root)
        match_run = MatchRun(
            run_id=run_id,
            lyrics_corpus_id="",  # TODO: should be extracted from matching
            timestamp=datetime.now(),
            input_text=input_text,
            config={},  # TODO: add matching config
            results=[],  # Will be populated below
        )

        # Match each token and add results to aggregate
        for token_data in token_data_list:
            reading = Reading(raw=token_data.reading)

            # Match token using strategy
            match_result: MatchResult = self.matching_strategy.match_token(
                surface=token_data.surface,
                reading=reading,
                lemma=token_data.lemma,
                pos=token_data.pos,
            )

            if match_result:
                # Add to aggregate (index is implicit in the array position)
                match_run.add_result(match_result)

        # Save the entire aggregate (MatchRun + results)
        saved_run_id = self.match_repository.save(match_run)

        return saved_run_id
