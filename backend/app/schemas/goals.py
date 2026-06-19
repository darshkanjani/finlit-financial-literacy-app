"""

Goals CRUD contract.
"""

from pydantic import BaseModel
from datetime import date


class GoalIn(BaseModel):
    goal_name: str
    target_amount: float
    current_amount: float = 0
    target_date: date | None = None


class GoalOut(BaseModel):
    id: str
    goal_name: str
    target_amount: float
    current_amount: float
    target_date: date | None
    status: str


class GoalForecastOut(BaseModel):
    goal_id: str
    months_needed: int | None
    monthly_savings_rate: float
    on_track: bool
    message: str
