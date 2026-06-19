"""

Stress test shapes. Keep it simple so frontend can graph month-by-month data.
"""

from pydantic import BaseModel


class StressTestIn(BaseModel):
    scenario_type: str  # "job_loss" | "promotion" | "emergency"
    params: dict = {}  # scenario-specific


class StressMonth(BaseModel):
    month: int
    income: float
    expenses: float
    savings_remaining: float
    net: float


class StressTestOut(BaseModel):
    id: str
    scenario_type: str
    params: dict = {}
    monthly_projections: list[dict] = []

    # Option A semantics:
    # - months_until_broke = FULL months survived (0..horizon)
    # - month_broke = first month where savings_remaining <= 0 (1..horizon)
    months_until_broke: int | None = None
    month_broke: int | None = None

    resilience_score: float = 0.0
    created_at: str | None = None


class StressTestSummaryOut(BaseModel):
    overall_score: float
    rating: str
    weakest_scenario: str | None = None


# Backward compatibility aliases
StressTestRunIn = StressTestIn
StressTestRunOut = StressTestOut