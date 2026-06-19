from app.services import chat_service


def test_chat_uses_literacy_specific_prompt_rules(db_session, make_user, monkeypatch):
    user = make_user(literacy_score=1)

    captured = {}

    def fake_call_llm_json(*, system, user, model="gpt-5-mini"):
        captured["system"] = system
        captured["user"] = user
        return {"reply": "Simple answer", "confidence": 0.9}

    monkeypatch.setattr(chat_service, "call_llm_json", fake_call_llm_json)
    monkeypatch.setattr(chat_service, "retrieve", lambda message, top_k=4: [])
    monkeypatch.setattr(chat_service, "to_chat_sources", lambda chunks: [])

    response = chat_service.chat_reply(db_session, user=user, message="How do I budget better?")

    assert response["response"] == "Simple answer"
    assert "User literacy_score is 1/5." in captured["system"]
    assert "Use plain English" in captured["system"]


def test_chat_history_persists_and_can_be_cleared(db_session, make_user, monkeypatch):
    user = make_user()

    monkeypatch.setattr(chat_service, "call_llm_json", lambda **kwargs: {"reply": "Stored answer", "confidence": 0.8})
    monkeypatch.setattr(chat_service, "retrieve", lambda message, top_k=4: [])
    monkeypatch.setattr(chat_service, "to_chat_sources", lambda chunks: [])

    post = chat_service.chat_reply(db_session, user=user, message="test history")
    assert post["response"] == "Stored answer"

    rows = chat_service.get_chat_history(db_session, user=user)
    assert len(rows) == 2
    assert rows[0]["role"] == "user"
    assert rows[0]["content"] == "test history"
    assert rows[1]["role"] == "assistant"
    assert rows[1]["content"] == "Stored answer"

    deleted = chat_service.clear_chat_history(db_session, user=user)
    assert deleted == 2
    assert chat_service.get_chat_history(db_session, user=user) == []
