"""

Goals logic:
- CRUD goals for a user
- Forecast endpoint: "are you on track given current savings rate?"

Savings rate definition (simple):
- monthly_savings_rate = monthly_income - total_expenses (from financial_profiles)
- if user has no profile, forecast returns a clear message (can't compute)

Forecast logic:
- remaining = target_amount - current_amount
- months_needed = ceil(remaining / monthly_savings_rate) if rate > 0
- months_until_deadline = months between today and target_date (rough)
- on_track = months_needed <= months_until_deadline

TODO (Ethan):
- keep goal status rules simple. status can be updated via PUT.
"""

import math
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Goal, FinancialProfile, User


def list_goals(db: Session, *, user: User) -> list[Goal]:
    return db.query(Goal).filter(Goal.user_id == user.id).order_by(Goal.created_at.desc()).all()


def create_goal(db: Session, *, user: User, payload: dict) -> Goal:
    goal = Goal(
        user_id=user.id,
        goal_name=payload["goal_name"],
        target_amount=float(payload["target_amount"]),
        current_amount=float(payload.get("current_amount", 0) or 0),
        target_date=payload.get("target_date"),
        status="active",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, *, user: User, goal_id: str, payload: dict) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    # update only provided fields
    for k in ["goal_name", "target_amount", "current_amount", "target_date", "status"]:
        if k in payload and payload[k] is not None:
            setattr(goal, k, payload[k])

    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, *, user: User, goal_id: str) -> None:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    db.delete(goal)
    db.commit()


def _monthly_savings_rate(db: Session, *, user: User) -> float | None:
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    if not profile:
        return None

    income = float(profile.monthly_income)
    expenses = (
        float(profile.rent or 0)
        + float(profile.bills or 0)
        + float(profile.subscriptions or 0)
        + float(profile.loan_repayments or 0)
        + float(profile.groceries or 0)
        + float(profile.transport or 0)
        + float(profile.entertainment or 0)
        + float(profile.eating_out or 0)
        + float(profile.clothing or 0)
        + float(profile.health or 0)
        + float(profile.other or 0)
    )
    return round(income - expenses, 2)


def forecast_goal(db: Session, *, user: User, goal_id: str) -> dict:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    rate = _monthly_savings_rate(db, user=user)
    if rate is None:
        return {
            "goal_id": str(goal.id),
            "months_needed": None,
            "monthly_savings_rate": 0.0,
            "on_track": False,
            "message": "Complete your profile first so we can estimate your monthly savings rate.",
        }

    if rate <= 0:
        return {
            "goal_id": str(goal.id),
            "months_needed": None,
            "monthly_savings_rate": float(rate),
            "on_track": False,
            "message": "Right now you’re not saving money each month, so this goal won’t move. Reduce expenses or increase income first.",
        }

    remaining = max(0.0, float(goal.target_amount) - float(goal.current_amount))
    months_needed = int(math.ceil(remaining / rate)) if remaining > 0 else 0

    # deadline check (rough months)
    on_track = True
    msg_parts = [f"At your current savings rate (£{rate}/month), you need about {months_needed} month(s) to reach this goal."]

    if goal.target_date:
        today = date.today()
        # rough month diff
        months_until_deadline = max(0, (goal.target_date.year - today.year) * 12 + (goal.target_date.month - today.month))
        on_track = months_needed <= months_until_deadline
        if on_track:
            msg_parts.append("You look on track for your deadline.")
        else:
            msg_parts.append("You might miss your deadline unless you save more each month.")

    return {
        "goal_id": str(goal.id),
        "months_needed": months_needed,
        "monthly_savings_rate": float(rate),
        "on_track": bool(on_track),
        "message": " ".join(msg_parts),
    }


def goal_to_out(goal: Goal) -> dict:
    return {
        "id": str(goal.id),
        "goal_name": goal.goal_name,
        "target_amount": float(goal.target_amount),
        "current_amount": float(goal.current_amount),
        "target_date": goal.target_date,
        "status": goal.status,
    }
