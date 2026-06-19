"""

CSV upload response:
- transactions for review UI (optional)
- category totals to prefill the onboarding form

We are NOT committing to storing raw transactions in DB.
Only final numbers go into financial_profiles.
"""

from pydantic import BaseModel


class CsvTransaction(BaseModel):
    date: str | None
    description: str
    amount: float
    suggested_category: str | None = None
    confidence: float | None = None
    method: str | None = None


class CsvUploadOut(BaseModel):
    transactions: list[CsvTransaction] = []
    category_totals: dict[str, float]
    warnings: list[str] = []
    parsed_count: int = 0
