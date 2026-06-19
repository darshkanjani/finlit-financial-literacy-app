"""

Dashboard is one endpoint that returns “everything the dashboard page needs”
so frontend doesn't have to call 4 endpoints on load.
"""

from pydantic import BaseModel
from app.schemas.spending import SpendingBreakdownOut
from app.schemas.goals import GoalOut


class ResilienceSummary(BaseModel):
    overall_score: float
    rating: str
    weakest_scenario: str | None = None


class DashboardOut(BaseModel):
    currency_code: str
    profile_monthly_income: float | None
    spending_breakdown: SpendingBreakdownOut | None
    resilience: ResilienceSummary | None
    goals: list[GoalOut]
    latest_advice_summary: str | None
    has_completed_profile: bool
    has_run_stress_test: bool
    has_set_goals: bool
