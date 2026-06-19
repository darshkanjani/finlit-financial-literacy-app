import pytest
from fastapi import HTTPException

from app.db.models import StressTestResult
from app.ml.stress_engine import ProfileSnapshot, run_scenario
from app.services import profile_service, stress_service


def _profile_payload(**overrides):
    payload = {
        "monthly_income": 3000,
        "currency_code": "GBP",
        "savings_buffer": 1200,
        "employment_status": "employed",
        "dependents_count": 0,
        "rent": 1000,
        "bills": 200,
        "subscriptions": 100,
        "groceries": 300,
        "transport": 150,
        "entertainment": 100,
        "eating_out": 100,
        "clothing": 50,
        "health": 50,
        "other": 0,
    }
    payload.update(overrides)
    return payload


def test_stress_engine_job_loss_returns_expected_shape():
    profile = ProfileSnapshot(
        monthly_income=3000,
        savings_buffer=1200,
        rent=1000,
        bills=200,
        groceries=300,
        transport=150,
        subscriptions=100,
        entertainment=100,
        eating_out=100,
        clothing=50,
        health=50,
        other=0,
    )

    result = run_scenario(
        profile,
        scenario_type="job_loss",
        params={"months": 6, "income_replacement": 0.0, "cutback_percent": 0.5},
    )

    assert result["scenario_type"] == "job_loss"
    assert len(result["monthly_projections"]) == 6
    assert result["month_broke"] is not None
    assert 0 <= result["resilience_score"] <= 10
    assert set(result["score_breakdown"].keys()) == {"survival", "buffer", "cashflow", "stability"}


def test_stress_service_runs_and_persists_job_loss(db_session, make_user, monkeypatch):
    monkeypatch.setattr(profile_service, "_run_initial_analysis", lambda *args, **kwargs: None)
    monkeypatch.setattr(stress_service, "load_model", lambda *args, **kwargs: None)
    user = make_user(literacy_score=2)
    profile_service.upsert_profile(db_session, user=user, payload_dict=_profile_payload())

    row = stress_service.run_and_store_stress_test(
        db_session,
        user=user,
        scenario_type="job_loss",
        params={"months": 6},
    )

    assert isinstance(row, StressTestResult)
    assert row.scenario_type == "job_loss"
    assert len(row.monthly_projections) == 6
    assert "score_breakdown" in row.params

    out = stress_service.stress_row_to_out(row)
    assert out["scenario_type"] == "job_loss"
    assert out["month_broke"] == stress_service._derive_month_broke_from_projections(row.monthly_projections)


def test_stress_service_uses_ml_cutback_when_prediction_available(db_session, make_user, monkeypatch):
    monkeypatch.setattr(profile_service, "_run_initial_analysis", lambda *args, **kwargs: None)
    monkeypatch.setattr(stress_service, "load_model", lambda *args, **kwargs: object())
    monkeypatch.setattr(stress_service, "predict_cutback_percent", lambda *args, **kwargs: 0.37)
    user = make_user(literacy_score=4)
    profile_service.upsert_profile(db_session, user=user, payload_dict=_profile_payload())

    row = stress_service.run_and_store_stress_test(db_session, user=user, scenario_type="job_loss", params={})

    assert row.params["ml_used"] is True
    assert row.params["cutback_percent"] == 0.37


def test_resilience_summary_averages_latest_per_scenario(db_session, make_user):
    user = make_user()
    db_session.add_all(
        [
            StressTestResult(user_id=user.id, scenario_type="job_loss", resilience_score=2.0, months_until_broke=0),
            StressTestResult(user_id=user.id, scenario_type="job_loss", resilience_score=4.0, months_until_broke=1),
            StressTestResult(user_id=user.id, scenario_type="promotion", resilience_score=8.0, months_until_broke=None),
        ]
    )
    db_session.commit()

    summary = stress_service.resilience_summary(db_session, user=user)

    assert summary["overall_score"] == 6.0
    assert summary["rating"] == "good"
    assert summary["weakest_scenario"] == "job_loss"


def test_stress_service_requires_profile(db_session, make_user):
    user = make_user()

    with pytest.raises(HTTPException) as exc:
        stress_service.run_and_store_stress_test(db_session, user=user, scenario_type="job_loss", params={})

    assert exc.value.status_code == 400
    assert "Complete your profile first" in exc.value.detail
