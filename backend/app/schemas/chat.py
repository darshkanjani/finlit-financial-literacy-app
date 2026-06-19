"""

Chat request/response.

Frontend can send last N messages (history) OR backend can store it (optional).
We support both:
- If payload.history is provided and non-empty, we use it.
- Else if store_history=True, we read recent history from DB.
"""

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class ChatMessageIn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatIn(BaseModel):
    message: str
    history: list[ChatMessageIn] = []
    store_history: bool = True  # if frontend doesn't send history, backend can store/load it


class ChatOut(BaseModel):
    response: str
    sources: list[dict] = []  # keep generic, works for RAG + future citations


class ChatHistoryMessageOut(BaseModel):
    role: str
    content: str
    sources: list[dict] = []
    created_at: str
