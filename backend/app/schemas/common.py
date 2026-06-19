"""

Shared small models we reuse everywhere so responses stay consistent.
Don’t over-engineer this. Keep it minimal.
"""

from pydantic import BaseModel


class MessageOut(BaseModel):
    message: str


class ErrorOut(BaseModel):
    detail: str
