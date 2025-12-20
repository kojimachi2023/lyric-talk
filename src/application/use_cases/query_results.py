"""QueryResultsUseCase implementation."""

from typing import Any, Dict, List, Optional

from src.domain.models.lyric_token import LyricToken
from src.domain.models.match_result import MatchResult, MatchType
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
            resolved_tokens = self._resolve_tokens(match_result)

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

    def _resolve_tokens(self, match_result: MatchResult) -> List[LyricToken]:
        """Resolve tokens from match result.

        For EXACT_SURFACE and EXACT_READING, use matched_token_ids.
        For MORA_COMBINATION, extract unique token_ids from mora_details.

        Args:
            match_result: Match result to resolve tokens for

        Returns:
            List of resolved LyricToken objects
        """
        resolved_tokens: List[LyricToken] = []

        # 単語・読み完全一致の場合
        if match_result.match_type in (MatchType.EXACT_SURFACE, MatchType.EXACT_READING):
            # Use matched_token_ids for exact matches
            for token_id in match_result.matched_token_ids:
                token = self.lyric_token_repository.get_by_id(token_id)
                if token:
                    resolved_tokens.append(token)

        elif match_result.match_type == MatchType.MORA_COMBINATION:
            # Extract unique token_ids from mora_details
            if match_result.mora_details:
                seen_token_ids: set[str] = set()
                for mora_detail in match_result.mora_details:
                    token_id = mora_detail.source_token_id
                    if token_id not in seen_token_ids:
                        seen_token_ids.add(token_id)
                        token = self.lyric_token_repository.get_by_id(token_id)
                        if token:
                            resolved_tokens.append(token)

        return resolved_tokens
