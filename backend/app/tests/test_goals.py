from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.services import goals_service, profile_service


def _profile_payload(**overrides):
    payload = {
        "monthly_income": 3000,
        "currency_code": "GBP",
        "savings_buffer": 1000,
        "rent": 1000,
        "bills": 200,
        "subscriptions": 50,
        "groceries": 250,
        "transport": 100,
        "entertainment": 100,
        "eating_out": 100,
        "clothing": 50,
        "health": 50,
        "other": 0,
    }
    payload.update(overrides)
    return payload


def test_create_update_and_delete_goal(db_session, make_user):
    user = make_user()

    goal = goals_service.create_goal(
        db_session,
        user=user,
        payload={"goal_name": "Emergency fund", "target_amount": 5000, "current_amount": 1500},
    )
    assert goal.goal_name == "Emergency fund"
    assert goal.status == "active"

    updated = goals_service.update_goal(
        db_session,
        user=user,
        goal_id=goal.id,
        payload={"current_amount": 2000, "status": "paused"},
    )
    assert updated.current_amount == 2000
    assert updated.status == "paused"

    listed = goals_service.list_goals(db_session, user=user)
    assert len(listed) == 1
    assert listed[0].id == goal.id

    goals_service.delete_goal(db_session, user=user, goal_id=goal.id)
    assert goals_service.list_goals(db_session, user=user) == []


def test_goal_forecast_without_profile_returns_clear_message(db_session, make_user):
    user = make_user()
    goal = goals_service.create_goal(
        db_session,
        user=user,
        payload={"goal_name": "Laptop", "target_amount": 1200, "current_amount": 200},
    )

    forecast = goals_service.forecast_goal(db_session, user=user, goal_id=goal.id)

    assert forecast["months_needed"] is None
    assert forecast["monthly_savings_rate"] == 0.0
    assert forecast["on_track"] is False
    assert "Complete your profile first" in forecast["message"]


def test_goal_forecast_uses_profile_savings_rate(db_session, make_user, monkeypatch):
    monkeypatch.setattr(profile_service, "_run_initial_analysis", lambda *args, **kwargs: None)
    user = make_user()
    profile_service.upsert_profile(db_session, user=user, payload_dict=_profile_payload())
    goal = goals_service.create_goal(
        db_session,
        user=user,
        payload={
            "goal_name": "Holiday",
            "target_amount": 3000,
            "current_amount": 1000,
            "target_date": date.today() + timedelta(days=180),
        },
    )

    forecast = goals_service.forecast_goal(db_session, user=user, goal_id=goal.id)

    assert forecast["monthly_savings_rate"] == 1100.0
    assert forecast["months_needed"] == 2
    assert forecast["on_track"] is True
    assert "At your current savings rate" in forecast["message"]


def test_update_missing_goal_raises_404(db_session, make_user):
    user = make_user()

    with pytest.raises(HTTPException) as exc:
        goals_service.update_goal(db_session, user=user, goal_id="missing", payload={"status": "done"})

    assert exc.value.status_code == 404
    assert exc.value.detail == "Goal not found"

