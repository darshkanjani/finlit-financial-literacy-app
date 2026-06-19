"""

What this file is:
- The response shape for the Spending Breakdown page.
- Frontend will render charts directly from this JSON.

What Ethan needs to do:
- Keep field names stable once frontend starts using them.
- Add more fields only if frontend asks.
"""

from pydantic import BaseModel


class SpendingCategory(BaseModel):
    name: str
    amount: float
    percentage: float
    type: str  # "need" or "want" or "savings"


class SpendingSummary(BaseModel):
    needs_percent: float
    wants_percent: float
    savings_percent: float
    target: dict[str, float] = {"needs": 50, "wants": 30, "savings": 20}


class SpendingFlag(BaseModel):
    category: str  # "needs" | "wants" | "savings"
    status: str  # "overspend" | "undersave"
    difference: float
    message: str


class SpendingBreakdownOut(BaseModel):
    categories: list[SpendingCategory]
    summary: SpendingSummary
    flags: list[SpendingFlag]
