"""QueryResultsUseCase implementation."""

from typing import Any, Dict, Optional

from src.domain.models.match_run import MatchRun
from src.domain.repositories.lyric_token_repository import LyricTokenRepository
from src.domain.repositories.match_repository import MatchRepository


class QueryResultsUseCase:
    """Use case for querying match results."""

    def __init__(
        self,
        match_repository: MatchRepository,
        lyric_token_repository: LyricTokenRepository,
    ):
        self.match_repository = match_repository
        self.lyric_token_repository = lyric_token_repository

    def execute(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Query results for a match run.

        Args:
            run_id: Match run ID

        Returns:
            Dict containing match_run and resolved results, or None if not found
        """
        # Get match run (aggregate) with results
        match_run: Optional[MatchRun] = self.match_repository.find_by_id(run_id)

        if match_run is None:
            return None

        # Resolve token information for each result
        resolved_results = []
        for match_result in match_run.results:
            resolved_tokens = []
            for token_id in match_result.matched_token_ids:
                token = self.lyric_token_repository.get_by_id(token_id)
                if token:
                    resolved_tokens.append(token)

            resolved_results.append(
                {
                    "match_result": match_result,
                    "resolved_tokens": resolved_tokens,
                }
            )

        return {
            "match_run": match_run,
            "results": resolved_results,
        }
