"""

AI helper schemas for "Goal Coaching Plan".

This endpoint does NOT update profile/goals by itself.
It returns suggestions, frontend shows them, user confirms, THEN frontend calls POST /profile.

Used by:
- POST /api/v1/advice/goal-plan
- app/services/plan_service.py
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GoalPlanIn(BaseModel):
    goal_id: str = Field(min_length=1)


class SuggestedChange(BaseModel):
    # must match FinancialProfile column names exactly
    field: str = Field(min_length=1)

    # current and suggested amounts for that field
    current: float = Field(ge=0)
    suggested: float = Field(ge=0)

    # suggested - current (so negative means "reduce spending here")
    delta: float

    # short reason for UI (e.g. "quick win cut", "reduce wants first")
    reason: str = Field(min_length=1, max_length=200)


class GoalPlanOut(BaseModel):
    summary: str = Field(min_length=1, max_length=800)

    # how much user needs to save per month to hit goal by deadline
    required_monthly_savings: float | None = Field(default=None)

    # list of category edits suggestion (frontend can render as checkbox list)
    suggested_changes: list[SuggestedChange] = Field(default_factory=list)

    # optional extra explanation bullets
    rationale: list[str] = Field(default_factory=list)

    # optional sources if you later add RAG grounding
    sources: list[dict] = Field(default_factory=list)

    confidence: float = Field(default=0.65, ge=0, le=1)
