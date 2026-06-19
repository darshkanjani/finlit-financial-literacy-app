"""

Advice schemas.

Advice = "one-shot report-ish output" used for dashboard/advice tab.
We store every advice response in AdviceHistory.

Sources:
- For RAG we don't have real URLs for local docs, so url can be None.
- If later you use web sources, fill url properly.
"""

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class AdviceSource(BaseModel):
    # Keep it simple for frontend: title + optional url.
    # Extra fields are optional so we can attach FAISS chunk metadata without breaking UI.
    title: str
    url: Optional[str] = None

    # Optional RAG metadata (safe to ignore in UI)
    chunk_id: Optional[str] = None
    score: Optional[float] = None


class AdviceIn(BaseModel):
    message: str


class AdviceOut(BaseModel):
    id: str | None = None
    question: str | None = None
    advice: str
    action_items: list[str] = []
    sources: list[AdviceSource] = []

    literacy_level_used: int = 3
    confidence: float = 0.6
    created_at: str | None = None


class AdviceHistoryOut(BaseModel):
    id: str
    question: str | None = None
    advice: str
    action_items: list[str] = []
    sources: list[AdviceSource] = []
    confidence: float = 0.6
    created_at: str
