"""

Spending Breakdown logic.

What it returns:
- list of categories (amount + % of income + type)
- summary of needs/wants/savings vs 50/30/20
- flags for overspending/undersaving

Important:
- Uses financial_profiles as the single source of truth
- Doesn't store anything new in DB (read-only calculation)

TODO (Ethan):
- Tweak which categories count as needs vs wants if you prefer.
- Keep names consistent so frontend chart labels don't break.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import FinancialProfile, User

NEEDS = {"rent", "bills", "groceries", "transport", "health", "loan_repayments"}
WANTS = {"subscriptions", "entertainment", "eating_out", "clothing", "other"}

ALL_FIELDS = [
    "rent",
    "bills",
    "subscriptions",
    "loan_repayments",
    "groceries",
    "transport",
    "entertainment",
    "eating_out",
    "clothing",
    "health",
    "other",
]


DISPLAY_NAMES = {
    "rent": "Rent",
    "bills": "Bills",
    "subscriptions": "Subscriptions",
    "loan_repayments": "Loan Repayments",
    "groceries": "Groceries",
    "transport": "Transport",
    "entertainment": "Entertainment",
    "eating_out": "Eating Out",
    "clothing": "Clothing",
    "health": "Health",
    "other": "Other",
}


def _pct(amount: float, income: float) -> float:
    if income <= 0:
        return 0.0
    return round((amount / income) * 100.0, 2)


def compute_breakdown(db: Session, *, user: User) -> dict:
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    income = float(profile.monthly_income)
    if income <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile monthly_income invalid")

    categories = []
    needs_total_pct = 0.0
    wants_total_pct = 0.0

    for f in ALL_FIELDS:
        amount = float(getattr(profile, f) or 0)
        p = _pct(amount, income)

        if f in NEEDS:
            ctype = "need"
            needs_total_pct += p
        elif f in WANTS:
            ctype = "want"
            wants_total_pct += p
        else:
            ctype = "want"

        categories.append(
            {
                "name": DISPLAY_NAMES.get(f, f),
                "amount": round(amount, 2),
                "percentage": p,
                "type": ctype,
            }
        )

    # savings = what's left of income after expenses
    total_expenses = sum(float(getattr(profile, f) or 0) for f in ALL_FIELDS)
    savings_amount = max(0.0, income - total_expenses)
    savings_pct = _pct(savings_amount, income)

    # Use percent totals based on our grouping rather than “100 - ...” to avoid rounding weirdness
    summary = {
        "needs_percent": round(needs_total_pct, 2),
        "wants_percent": round(wants_total_pct, 2),
        "savings_percent": round(savings_pct, 2),
        "target": {"needs": 50, "wants": 30, "savings": 20},
    }

    flags = []

    if needs_total_pct > 50:
        diff = round(needs_total_pct - 50, 2)
        flags.append(
            {
                "category": "needs",
                "status": "overspend",
                "difference": diff,
                "message": f"Your essential spending is {diff}% above the recommended 50%",
            }
        )

    if wants_total_pct > 30:
        diff = round(wants_total_pct - 30, 2)
        flags.append(
            {
                "category": "wants",
                "status": "overspend",
                "difference": diff,
                "message": f"Your non-essential spending is {diff}% above the recommended 30%",
            }
        )

    if savings_pct < 20:
        diff = round(20 - savings_pct, 2)
        flags.append(
            {
                "category": "savings",
                "status": "undersave",
                "difference": diff,
                "message": f"Your savings rate is {diff}% below the recommended 20%",
            }
        )

    return {"categories": categories, "summary": summary, "flags": flags}
