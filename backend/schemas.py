from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LoginRequest(BaseModel):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: Optional[int] = 5
    debug: Optional[bool] = False

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
    chunk_id: str
    chunk_type: Optional[str]

class DebugInfo(BaseModel):
    latency_ms: int
    top_k: int
    embedding_model: str
    retrieval_strategy: str

class AskResponse(BaseModel):
    question: str
    answer: str
    context: List[SourceMetadata]
    debug: Optional[DebugInfo]

class ConfigResponse(BaseModel):
    available_chunk_strategies: List[str]
    default_top_k: int
    supported_languages: List[str]
