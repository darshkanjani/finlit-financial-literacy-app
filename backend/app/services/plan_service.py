"""

Goal coaching plan generator.

This combines deterministic math + optional LLM:
1) Deterministic:
   - compute required monthly savings to meet goal by deadline
   - compute current savings rate from profile (income - expenses)
2) AI (optional):
   - propose which categories to adjust and by how much, in a structured list
   - keep it grounded in the user's actual numbers

Output:
- GoalPlanOut dict (validated by schema in endpoint)

Design rule:
- Endpoint returns suggestions only. No DB writes here.
"""

import math
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User, Goal, FinancialProfile
from app.services.llm_service import call_llm_json


PROFILE_FIELDS = ["rent","bills","subscriptions","loan_repayments","groceries","transport","entertainment","eating_out","clothing","health","other"]


def build_goal_plan(db: Session, *, user: User, goal_id: str) -> dict:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    if not profile:
        return {
            "summary": "Complete your profile first so we can suggest a realistic plan.",
            "required_monthly_savings": None,
            "suggested_changes": [],
            "rationale": ["No profile found, so we don’t know your income/expenses yet."],
            "sources": [],
            "confidence": 0.5,
        }

    income = float(profile.monthly_income)
    expenses = sum(float(getattr(profile, f) or 0) for f in PROFILE_FIELDS)
    current_savings_rate = income - expenses

    remaining = max(0.0, float(goal.target_amount) - float(goal.current_amount))

    required = None
    if goal.target_date:
        today = date.today()
        months_left = max(1, (goal.target_date.year - today.year) * 12 + (goal.target_date.month - today.month))
        required = round(remaining / months_left, 2)

    # If we don't have a date, we can still suggest a plan based on "increase savings"
    if required is None:
        required = max(0.0, round(min(remaining, max(current_savings_rate, 0.0)), 2))

    summary = f"Your current estimated savings rate is £{round(current_savings_rate,2)}/month."
    summary += f" To hit this goal, aim for about £{required}/month."

    # LLM enhancement: propose category edits, but MUST be JSON and MUST use valid fields.
    system = (
        "You are a budgeting coach. Return JSON only. "
        "Output fields: summary, required_monthly_savings, suggested_changes (list of {field,current,suggested,delta,reason}), rationale, confidence. "
        f"Allowed fields for suggested_changes.field: {PROFILE_FIELDS}. "
        "Do NOT invent fields."
    )

    # provide compact context
    profile_context = {f: float(getattr(profile, f) or 0) for f in PROFILE_FIELDS}
    user_msg = (
        f"Goal: name={goal.goal_name}, target={goal.target_amount}, current={goal.current_amount}, target_date={goal.target_date}\n"
        f"Income={income}, current_expenses={expenses}, current_savings_rate={current_savings_rate}\n"
        f"Required_monthly_savings={required}\n"
        f"Profile breakdown: {profile_context}\n"
        "Propose realistic cuts starting with wants (subscriptions, entertainment, eating_out) before needs."
    )

    llm = call_llm_json(system=system, user=user_msg)

    if not llm:
        # Heuristic fallback: suggest trimming wants a bit
        suggestions = []
        for f in ["eating_out", "entertainment", "subscriptions"]:
            cur = float(getattr(profile, f) or 0)
            if cur > 0:
                suggested = round(cur * 0.7, 2)  # 30% cut
                suggestions.append(
                    {"field": f, "current": cur, "suggested": suggested, "delta": round(suggested - cur, 2), "reason": "quick win cut"}
                )
        return {
            "summary": summary,
            "required_monthly_savings": float(required),
            "suggested_changes": suggestions,
            "rationale": ["Starter plan: reduce some wants categories first, then re-run forecast."],
            "sources": [],
            "confidence": 0.65,
        }

    # basic safety: strip unknown fields from AI suggestions
    cleaned = []
    for item in llm.get("suggested_changes", []) or []:
        field = item.get("field")
        if field in PROFILE_FIELDS:
            cleaned.append(item)
    llm["suggested_changes"] = cleaned

    llm.setdefault("required_monthly_savings", float(required))
    llm.setdefault("confidence", 0.75)
    return llm
