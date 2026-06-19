from app.db.models import Goal, StressTestResult
from app.services import dashboard_service, profile_service


def _profile_payload(**overrides):
    payload = {
        "monthly_income": 4000,
        "currency_code": "USD",
        "savings_buffer": 2500,
        "rent": 1200,
        "bills": 220,
        "subscriptions": 50,
        "groceries": 320,
        "transport": 180,
    }
    payload.update(overrides)
    return payload


def test_dashboard_fresh_user(db_session, make_user):
    user = make_user()

    dashboard = dashboard_service.build_dashboard(db_session, user=user)

    assert dashboard["currency_code"] == "GBP"
    assert dashboard["profile_monthly_income"] is None
    assert dashboard["spending_breakdown"] is None
    assert dashboard["resilience"] is None
    assert dashboard["goals"] == []
    assert dashboard["has_completed_profile"] is False
    assert dashboard["has_run_stress_test"] is False
    assert dashboard["has_set_goals"] is False


def test_dashboard_after_profile_returns_currency_and_breakdown(db_session, make_user, monkeypatch):
    monkeypatch.setattr(profile_service, "_run_initial_analysis", lambda *args, **kwargs: None)
    user = make_user()
    profile_service.upsert_profile(db_session, user=user, payload_dict=_profile_payload())

    goal = Goal(user_id=user.id, goal_name="Emergency fund", target_amount=5000, current_amount=1000, status="active")
    stress_low = StressTestResult(user_id=user.id, scenario_type="job_loss", resilience_score=4.0, months_until_broke=2)
    stress_high = StressTestResult(user_id=user.id, scenario_type="promotion", resilience_score=8.8, months_until_broke=None)
    db_session.add_all([goal, stress_low, stress_high])
    db_session.commit()

    dashboard = dashboard_service.build_dashboard(db_session, user=user)

    assert dashboard["currency_code"] == "USD"
    assert dashboard["profile_monthly_income"] == 4000.0
    assert dashboard["spending_breakdown"] is not None
    assert dashboard["spending_breakdown"]["summary"]["needs_percent"] == 48.0
    assert dashboard["spending_breakdown"]["summary"]["wants_percent"] == 1.25
    assert dashboard["spending_breakdown"]["summary"]["savings_percent"] == 50.75
    assert dashboard["resilience"]["overall_score"] == 6.4
    assert dashboard["resilience"]["weakest_scenario"] == "job_loss"
    assert dashboard["goals"][0]["goal_name"] == "Emergency fund"
    assert dashboard["has_completed_profile"] is True
    assert dashboard["has_run_stress_test"] is True
    assert dashboard["has_set_goals"] is True
