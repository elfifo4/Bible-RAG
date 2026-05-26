from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

class LoginRequest(BaseModel):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

RetrievalStrategy = Literal[
    "hybrid",
    "dense_only",
    "lexical_only",
    "single_verse",
    "sliding_window"
]

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: Optional[int] = Field(5, ge=1, le=20)
    debug: Optional[bool] = True
    retrieval_strategy: Optional[RetrievalStrategy] = "hybrid"

class SourceMetadata(BaseModel):
    ref: str
    ref_en: str
    book: Optional[str]
    book_en: Optional[str]
    chapter: Optional[int]
    verse_start: Optional[int]
    verse_end: Optional[int]
    text: str
    score: float
    dense_score: Optional[float] = 0.0
    lexical_score: Optional[float] = 0.0
    chunk_id: str
    chunk_type: Optional[str]

class DebugInfo(BaseModel):
    latency_ms: int
    top_k: int
    embedding_model: str
    retrieval_strategy: str

class Chunk(BaseModel):
    chunk_id: str
    text: str
    display_text: str
    score: float
    dense_score: Optional[float] = 0.0
    lexical_score: Optional[float] = 0.0
    metadata: Dict[str, Any]

class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    retrieved_chunks: List[Chunk]
    context: List[Chunk]  # Alias for compatibility
    debug: Optional[DebugInfo]

class CompareRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: Optional[int] = Field(5, ge=1, le=10)
    strategies: List[RetrievalStrategy] = ["hybrid", "dense_only", "lexical_only"]

class CompareResponse(BaseModel):
    question: str
    results: Dict[str, AskResponse]
    total_latency_ms: int

class ConfigResponse(BaseModel):
    available_chunk_strategies: List[str]
    default_top_k: int
    supported_languages: List[str]

class StrategyMetrics(BaseModel):
    strategy: str
    questions_count: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    recall_at_5: float
    mrr: float

class EvalSummaryResponse(BaseModel):
    strategies: Dict[str, StrategyMetrics]

class QuestionEvalResult(BaseModel):
    question: str
    strategy: str
    relevant_found: bool
    first_relevant_rank: Optional[int]
    hit_at_1: bool
    hit_at_3: bool
    hit_at_5: bool
    recall_at_5: float
    mrr: float
    retrieved_refs: List[str]
    expected: Optional[Dict[str, Any]]

class EvalQuestionsResponse(BaseModel):
    results: List[QuestionEvalResult]
