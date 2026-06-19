"""

AI helper schemas for "Natural Language Goals".

These do NOT write to DB.
They only return a suggested structured goal that the user can review,
then frontend calls normal POST /goals to save.

Used by:
- POST /api/v1/goals/parse
- app/services/goals_ai_service.py
"""

from __future__ import annotations

from datetime import date
from pydantic import BaseModel, Field


class GoalParseIn(BaseModel):
    # raw user text like: "I want an emergency fund in 6 months"
    text: str = Field(min_length=3, max_length=500)


class GoalParseOut(BaseModel):
    # suggested structured goal (frontend shows a preview card)
    goal_name: str = Field(min_length=1, max_length=80)
    target_amount: float = Field(gt=0)
    target_date: date | None = None
    current_amount: float = Field(default=0, ge=0)

    # transparency for markers: what assumptions did we make?
    assumptions: list[str] = Field(default_factory=list)

    # just a rough score so UI can show "AI confidence"
    confidence: float = Field(default=0.65, ge=0, le=1)
