"""QueryResultsUseCase implementation."""

from typing import List, Optional

from src.application.dtos.query_results_dto import (
    InputTokenDto,
    LyricTokenDto,
    MatchRunMetaDto,
    MatchStatsDto,
    MoraTraceDto,
    MoraTraceItemDto,
    QueryMatchItemDto,
    QueryResultsDto,
    QuerySummaryDto,
    ReconstructionStepDto,
)
from src.domain.models.lyric_token import LyricToken
from src.domain.models.match_result import MatchResult, MatchType
from src.domain.models.match_run import MatchRun
from src.domain.repositories.unit_of_work import UnitOfWork


class QueryResultsUseCase:
    """Use case for querying match results."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
    ):
        self.unit_of_work = unit_of_work

    def execute(self, run_id: str) -> Optional[QueryResultsDto]:
        """Query results for a match run.

        Args:
            run_id: Match run ID

        Returns:
            QueryResultsDto containing match_run and resolved results, or None if not found
        """
        # Get match run (aggregate) with results
        match_run: Optional[MatchRun] = self.unit_of_work.match_repository.find_by_id(run_id)

        if match_run is None:
            return None

        # Build match run metadata
        match_run_meta = MatchRunMetaDto(
            run_id=match_run.run_id,
            lyrics_corpus_id=match_run.lyrics_corpus_id,
            timestamp=match_run.timestamp,
            input_text=match_run.input_text,
        )

        # Process each match result into QueryMatchItemDto
        items: List[QueryMatchItemDto] = []
        reconstruction_steps: List[ReconstructionStepDto] = []
        stats = {
            "exact_surface": 0,
            "exact_reading": 0,
            "mora_combination": 0,
            "no_match": 0,
        }

        for match_result in match_run.results:
            # Resolve tokens
            resolved_tokens = self._resolve_tokens(match_result)

            # Convert to DTOs
            lyric_token_dtos = [self._to_lyric_token_dto(t) for t in resolved_tokens]
            input_dto = InputTokenDto(
                surface=match_result.input_token, reading=match_result.input_reading
            )

            # Build mora trace if applicable
            mora_trace = self._build_mora_trace(match_result)

            # Build query match item
            item = QueryMatchItemDto(
                input=input_dto,
                match_type=match_result.match_type,
                chosen_lyrics_tokens=lyric_token_dtos,
                mora_trace=mora_trace,
            )
            items.append(item)

            # Build reconstruction step
            chosen_surface, chosen_reading = self._build_chosen_text(match_result, resolved_tokens)
            reconstruction_step = ReconstructionStepDto(
                input=input_dto,
                match_type=match_result.match_type,
                chosen_surface=chosen_surface,
                chosen_reading=chosen_reading,
                chosen_lyrics_tokens=lyric_token_dtos,
                mora_trace=mora_trace,
            )
            reconstruction_steps.append(reconstruction_step)

            # Update stats
            if match_result.match_type == MatchType.EXACT_SURFACE:
                stats["exact_surface"] += 1
            elif match_result.match_type == MatchType.EXACT_READING:
                stats["exact_reading"] += 1
            elif match_result.match_type == MatchType.MORA_COMBINATION:
                stats["mora_combination"] += 1
            elif match_result.match_type == MatchType.NO_MATCH:
                stats["no_match"] += 1

        # Build summary reconstructed text
        reconstructed_surface = "".join(step.chosen_surface or "" for step in reconstruction_steps)
        reconstructed_reading = "".join(step.chosen_reading for step in reconstruction_steps)

        summary = QuerySummaryDto(
            reconstructed_surface=reconstructed_surface,
            reconstructed_reading=reconstructed_reading,
            reconstruction_steps=reconstruction_steps,
            stats=MatchStatsDto(
                exact_surface_count=stats["exact_surface"],
                exact_reading_count=stats["exact_reading"],
                mora_combination_count=stats["mora_combination"],
                no_match_count=stats["no_match"],
            ),
        )

        return QueryResultsDto(match_run=match_run_meta, items=items, summary=summary)

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
                token = self.unit_of_work.lyric_token_repository.get_by_id(token_id)
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
                        token = self.unit_of_work.lyric_token_repository.get_by_id(token_id)
                        if token:
                            resolved_tokens.append(token)

        return resolved_tokens

    def _to_lyric_token_dto(self, token: LyricToken) -> LyricTokenDto:
        """Convert LyricToken to LyricTokenDto."""
        return LyricTokenDto(
            token_id=token.token_id,
            surface=token.surface,
            reading=token.reading.normalized,
            lemma=token.lemma,
            pos=token.pos,
        )

    def _build_mora_trace(self, match_result: MatchResult) -> Optional[MoraTraceDto]:
        """Build mora trace for mora combination matches."""
        if match_result.match_type != MatchType.MORA_COMBINATION or not match_result.mora_details:
            return None

        items = [
            MoraTraceItemDto(
                mora=detail.mora,
                source_token_id=detail.source_token_id,
                mora_index=detail.mora_index,
            )
            for detail in match_result.mora_details
        ]

        return MoraTraceDto(items=items)

    def _build_chosen_text(
        self, match_result: MatchResult, resolved_tokens: List[LyricToken]
    ) -> tuple[Optional[str], str]:
        """Build chosen surface and reading for reconstruction.

        Args:
            match_result: Match result
            resolved_tokens: Resolved lyric tokens

        Returns:
            Tuple of (chosen_surface, chosen_reading)
        """
        if match_result.match_type in (MatchType.EXACT_SURFACE, MatchType.EXACT_READING):
            # For exact matches, concatenate token surfaces and readings
            chosen_surface = "".join(t.surface for t in resolved_tokens)
            chosen_reading = "".join(t.reading.normalized for t in resolved_tokens)
            return chosen_surface, chosen_reading

        elif match_result.match_type == MatchType.MORA_COMBINATION:
            # For mora combination, concatenate moras from mora_details
            if match_result.mora_details:
                chosen_reading = "".join(detail.mora for detail in match_result.mora_details)
                # Surface is not meaningful for mora combination, use None or a description
                return None, chosen_reading

        # No match or other cases
        return None, ""
