"""QueryResults DTOs for CLI display."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from src.domain.models.match_result import MatchType


class InputTokenDto(BaseModel):
    """Input token information."""

    surface: str
    reading: str

    model_config = {"frozen": True}


class LyricTokenDto(BaseModel):
    """Lyric token information for display."""

    token_id: str
    surface: str
    reading: str
    lemma: str
    pos: str

    model_config = {"frozen": True}


class MoraTraceItemDto(BaseModel):
    """Mora trace item showing mora to token mapping."""

    mora: str
    source_token_id: str
    mora_index: int

    model_config = {"frozen": True}


class MoraTraceDto(BaseModel):
    """Mora trace information for mora combination matches."""

    items: List[MoraTraceItemDto]

    model_config = {"frozen": True}


class ReconstructionStepDto(BaseModel):
    """Single step in the reconstruction process."""

    input: InputTokenDto
    match_type: MatchType
    chosen_surface: Optional[str] = None
    chosen_reading: str
    chosen_lyrics_tokens: List[LyricTokenDto]
    mora_trace: Optional[MoraTraceDto] = None

    model_config = {"frozen": True}


class MatchStatsDto(BaseModel):
    """Statistics about match types."""

    exact_surface_count: int = 0
    exact_reading_count: int = 0
    mora_combination_count: int = 0
    no_match_count: int = 0

    model_config = {"frozen": True}


class QuerySummaryDto(BaseModel):
    """Summary of query results with reconstructed text."""

    reconstructed_surface: str
    reconstructed_reading: str
    reconstruction_steps: List[ReconstructionStepDto]
    stats: MatchStatsDto

    model_config = {"frozen": True}


class QueryMatchItemDto(BaseModel):
    """Single match item in query results."""

    input: InputTokenDto
    match_type: MatchType
    chosen_lyrics_tokens: List[LyricTokenDto]
    mora_trace: Optional[MoraTraceDto] = None

    model_config = {"frozen": True}


class MatchRunMetaDto(BaseModel):
    """Match run metadata for query results."""

    run_id: str
    lyrics_corpus_id: str
    timestamp: datetime
    input_text: str

    model_config = {"frozen": True}


class QueryResultsDto(BaseModel):
    """Query results with reconstructed summary."""

    match_run: MatchRunMetaDto
    items: List[QueryMatchItemDto]
    summary: QuerySummaryDto

    model_config = {"frozen": True}
