"""

Onboarding form models.

Notes:
- We store final validated numbers in financial_profiles.
- Literacy answers are optional; if provided, backend can compute literacy_score and store in users table.
- Keep fields consistent with the DB column names so mapping is easy.

NEW (Darsh update request):
- Added lightweight context fields to improve stress tests + advice/chat personalisation:
  - age_band (broad, not exact age)
  - employment_status
  - occupation_category (broad)
  - dependents_count
  - savings_buffer (cash buffer / current savings)
"""

from pydantic import BaseModel, Field


class ProfileIn(BaseModel):
    monthly_income: float = Field(gt=0)
    currency_code: str = "GBP"

    # NEW: lightweight context (all optional / safe defaults)
    # Keep these broad + non-invasive. We can validate more strictly later if needed.
    age_band: str | None = None  # e.g. "18-24", "25-34", "35-44", "45-54", "55+"
    employment_status: str | None = None  # e.g. "student", "employed", "self_employed", "unemployed"
    occupation_category: str | None = None  # e.g. "tech", "finance", "retail", "healthcare", "other"
    dependents_count: int = Field(default=0, ge=0, le=20)
    savings_buffer: float = Field(default=0, ge=0)

    # fixed-ish
    rent: float = Field(default=0, ge=0)
    bills: float = Field(default=0, ge=0)
    subscriptions: float = Field(default=0, ge=0)
    loan_repayments: float = Field(default=0, ge=0)

    # variable-ish
    groceries: float = Field(default=0, ge=0)
    transport: float = Field(default=0, ge=0)
    entertainment: float = Field(default=0, ge=0)
    eating_out: float = Field(default=0, ge=0)
    clothing: float = Field(default=0, ge=0)
    health: float = Field(default=0, ge=0)
    other: float = Field(default=0, ge=0)

    # optional literacy scoring inputs
    manual_literacy_score: int | None = Field(default=None, ge=1, le=5)
    literacy_answers: list[int] | None = None


class ProfileOut(BaseModel):
    profile_id: str
    monthly_income: float
    currency_code: str

    # NEW: echo back context so frontend can show what’s saved
    age_band: str | None
    employment_status: str | None
    occupation_category: str | None
    dependents_count: int
    savings_buffer: float

    # echo back stored values (frontend can show what’s saved)
    rent: float
    bills: float
    subscriptions: float
    loan_repayments: float
    groceries: float
    transport: float
    entertainment: float
    eating_out: float
    clothing: float
    health: float
    other: float

    # computed summary fields (useful for frontend + spending tab)
    total_expenses: float
    savings_potential: float

    literacy_score: int
