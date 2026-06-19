"""

Natural language goals parser.

Inputs:
- user text (e.g. "emergency fund in 6 months")

Context available:
- user's profile (income + expenses) helps guess target_amount
  Example:
    emergency fund = 3 months of NEEDS (or total expenses), depending on assumption.

Output:
- GoalParseOut

Design choice:
- This service *suggests* a goal, it does not create it.
- Always include assumptions for transparency.
"""

from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.db.models import User, FinancialProfile
from app.services.llm_service import call_llm_json


def parse_goal_text(db: Session, *, user: User, text: str) -> dict:
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()

    # Basic heuristic fallback (works even if LLM isn't wired):
    assumptions = []
    target_amount = 1000.0
    target_date = None

    if profile:
        # crude emergency fund estimate: 3 months of "needs"
        needs = float(profile.rent or 0) + float(profile.bills or 0) + float(profile.groceries or 0) + float(profile.transport or 0) + float(profile.health or 0) + float(profile.loan_repayments or 0)
        multiplier = 3
        if int(profile.dependents_count or 0) >= 1:
            multiplier = 4  # simple, defensible
            assumptions.append("Assumed emergency fund = 4 months of essential spending because dependents > 0.")
        else:
            assumptions.append("Assumed emergency fund = 3 months of essential spending (needs).")

        target_amount = round(needs * multiplier, 2)

    # If user said "in X months", we can guess a date (super rough)
    if "6 month" in text.lower() or "6 months" in text.lower():
        target_date = date.today() + timedelta(days=30 * 6)
        assumptions.append("Assumed timeline counted from today.")

    # LLM enhancement (optional):
    # - You can use LLM to extract goal_name + timeline + intent cleanly.
    # - Keep it JSON-only and validate with Pydantic at the endpoint layer.
    system = (
        "You convert a user's natural language goal into JSON fields: "
        "goal_name, target_amount, target_date, current_amount, assumptions, confidence. "
        "Return JSON only."
    )
    user_msg = f"User text: {text}\nKnown default suggestion: target_amount={target_amount}, target_date={target_date}"

    llm = call_llm_json(system=system, user=user_msg)

    # If LLM returns nothing (stub), fall back to heuristic output.
    if not llm:
        return {
            "goal_name": "Emergency fund" if "emergency" in text.lower() else "Goal",
            "target_amount": target_amount,
            "target_date": target_date,
            "current_amount": 0,
            "assumptions": assumptions,
            "confidence": 0.65,
        }

    # Otherwise trust LLM output but keep assumptions if missing
    llm.setdefault("assumptions", assumptions)
    llm.setdefault("confidence", 0.7)
    llm.setdefault("current_amount", 0)
    return llm
