from app.services import advice_service, profile_service


def _profile_payload(**overrides):
    payload = {
        "monthly_income": 3000,
        "currency_code": "GBP",
        "savings_buffer": 1500,
        "rent": 950,
        "bills": 180,
        "groceries": 280,
        "transport": 120,
    }
    payload.update(overrides)
    return payload


def test_advice_uses_literacy_specific_prompt_rules(db_session, make_user, monkeypatch):
    monkeypatch.setattr(profile_service, "_run_initial_analysis", lambda *args, **kwargs: None)
    user = make_user(literacy_score=3)
    profile_service.upsert_profile(db_session, user=user, payload_dict=_profile_payload(manual_literacy_score=5))

    captured = {}

    def fake_call_llm_json(*, system, user, model="gpt-5-mini"):
        captured["system"] = system
        return {"advice_text": "Detailed advice", "action_items": ["A", "B"], "confidence": 0.9}

    monkeypatch.setattr(advice_service, "call_llm_json", fake_call_llm_json)
    monkeypatch.setattr(advice_service, "retrieve", lambda message, top_k=4: [])
    monkeypatch.setattr(advice_service, "to_advice_sources", lambda chunks: [])

    response = advice_service.generate_advice(db_session, user=user, message="How strong is my plan?")
    assert response["advice"] == "Detailed advice"
    assert response["literacy_level_used"] == 5
    assert "User literacy_score is 5/5." in captured["system"]
    assert "moderate technical detail" in captured["system"]


def test_advice_history_and_clear(db_session, make_user, monkeypatch):
    user = make_user()

    monkeypatch.setattr(advice_service, "call_llm_json", lambda **kwargs: {})
    monkeypatch.setattr(advice_service, "retrieve", lambda message, top_k=4: [])
    monkeypatch.setattr(advice_service, "to_advice_sources", lambda chunks: [])

    response = advice_service.generate_advice(db_session, user=user, message="What should I do?")
    assert response["advice"]

    history = advice_service.list_advice_history(db_session, user=user)
    assert len(history) == 1
    assert history[0]["question"] == "What should I do?"

    deleted = advice_service.clear_advice_history(db_session, user=user)
    assert deleted == 1
    assert advice_service.list_advice_history(db_session, user=user) == []
