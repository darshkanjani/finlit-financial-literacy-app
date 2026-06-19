"""

Dashboard aggregation.

The point:
- Frontend calls ONE endpoint on dashboard load.
- Backend bundles:
  - spending breakdown (if profile exists)
  - resilience summary (if stress tests exist)
  - goals list
  - latest advice summary (if exists)
  - booleans: has_profile, has_goals, has_stress

This file should orchestrate, not contain heavy logic.
"""

from sqlalchemy.orm import Session

from app.db.models import User, FinancialProfile, Goal, StressTestResult, AdviceHistory
from app.services.spending_service import compute_breakdown
from app.services.goals_service import list_goals, goal_to_out
from app.services.profile_service import get_user_currency_code


def _latest_stress_by_scenario(rows: list[StressTestResult]) -> list[StressTestResult]:
    latest: dict[str, StressTestResult] = {}
    for row in rows:
        scenario = getattr(row, "scenario_type", "") or ""
        existing = latest.get(scenario)
        if existing is None:
            latest[scenario] = row
            continue
        if getattr(row, "created_at", None) and getattr(existing, "created_at", None):
            if row.created_at > existing.created_at:
                latest[scenario] = row
    return list(latest.values())


def build_dashboard(db: Session, *, user: User) -> dict:
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    has_profile = profile is not None

    goals = list_goals(db, user=user)
    has_goals = len(goals) > 0

    stress_rows = db.query(StressTestResult).filter(StressTestResult.user_id == user.id).all()
    has_stress = len(stress_rows) > 0

    advice = (
        db.query(AdviceHistory)
        .filter(AdviceHistory.user_id == user.id)
        .order_by(AdviceHistory.created_at.desc())
        .first()
    )

    spending_breakdown = None
    if has_profile:
        # compute_breakdown already throws clean errors if profile missing, but we guard anyway
        spending_breakdown = compute_breakdown(db, user=user)

    resilience = None
    if has_stress:
        latest_rows = _latest_stress_by_scenario(stress_rows)
        scores = [float(r.resilience_score) for r in latest_rows if r.resilience_score is not None]
        if scores:
            avg = sum(scores) / len(scores)
            if avg < 3:
                rating = "low"
            elif avg < 5:
                rating = "moderate"
            elif avg < 7:
                rating = "good"
            elif avg < 8.5:
                rating = "strong"
            else:
                rating = "excellent"

            # weakest scenario: smallest score
            weakest = min(latest_rows, key=lambda r: float(r.resilience_score or 0))
            resilience = {
                "overall_score": round(avg, 2),
                "rating": rating,
                "weakest_scenario": getattr(weakest, "scenario_type", None),
            }

    # Fallback: if no advice exists yet (e.g. user bypassed normal onboarding flow),
    # generate welcome advice now so dashboard is never empty.
    if not advice and has_profile:
        try:
            from app.services.advice_service import generate_welcome_advice
            advice = generate_welcome_advice(db, user=user)
        except Exception:
            pass  # Never block dashboard load

    latest_advice_summary = None
    if advice and getattr(advice, "advice_text", None):
        # Keep it short so dashboard isn't a wall of text
        latest_advice_summary = advice.advice_text[:240] + ("..." if len(advice.advice_text) > 240 else "")

    return {
        "currency_code": get_user_currency_code(db, user_id=user.id),
        "profile_monthly_income": float(profile.monthly_income) if has_profile else None,
        "spending_breakdown": spending_breakdown,
        "resilience": resilience,
        "goals": [goal_to_out(g) for g in goals],
        "latest_advice_summary": latest_advice_summary,
        "has_completed_profile": has_profile,
        "has_run_stress_test": has_stress,
        "has_set_goals": has_goals,
    }
