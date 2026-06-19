import pytest
from fastapi import HTTPException

from app.services import profile_service


def _payload(**overrides):
    payload = {
        "monthly_income": 3200,
        "currency_code": "AED",
        "savings_buffer": 1800,
        "rent": 1100,
        "bills": 220,
        "subscriptions": 40,
        "loan_repayments": 0,
        "groceries": 300,
        "transport": 120,
        "entertainment": 90,
        "eating_out": 85,
        "clothing": 30,
        "health": 20,
        "other": 15,
    }
    payload.update(overrides)
    return payload


def test_profile_roundtrip_stores_currency_and_manual_literacy(db_session, make_user, monkeypatch):
    monkeypatch.setattr(profile_service, "_run_initial_analysis", lambda *args, **kwargs: None)
    user = make_user(literacy_score=2)

    profile = profile_service.upsert_profile(
        db_session,
        user=user,
        payload_dict=_payload(manual_literacy_score=5),
    )
    out = profile_service.profile_to_out(db=db_session, profile=profile, user=user)

    assert out["monthly_income"] == 3200.0
    assert out["currency_code"] == "AED"
    assert out["literacy_score"] == 5
    assert out["total_expenses"] == pytest.approx(2020.0)
    assert out["savings_potential"] == pytest.approx(1180.0)


def test_profile_literacy_quiz_updates_score(db_session, make_user, monkeypatch):
    monkeypatch.setattr(profile_service, "_run_initial_analysis", lambda *args, **kwargs: None)
    user = make_user(literacy_score=1)

    profile_service.upsert_profile(
        db_session,
        user=user,
        payload_dict=_payload(currency_code="USD", literacy_answers=[4, 5, 4]),
    )

    assert user.literacy_score == 4
    assert profile_service.get_user_currency_code(db_session, user_id=user.id) == "USD"


def test_profile_keeps_existing_literacy_if_no_new_literacy_input(db_session, make_user, monkeypatch):
    monkeypatch.setattr(profile_service, "_run_initial_analysis", lambda *args, **kwargs: None)
    user = make_user(literacy_score=4)

    profile_service.upsert_profile(db_session, user=user, payload_dict=_payload())

    assert user.literacy_score == 4


def test_profile_validation_rejects_invalid_income(db_session, make_user):
    user = make_user()

    with pytest.raises(HTTPException) as exc:
        profile_service.upsert_profile(db_session, user=user, payload_dict=_payload(monthly_income=0))

    assert exc.value.status_code == 400
    assert exc.value.detail == "monthly_income must be > 0"
