"""

Chat orchestration.

What it does:
- rebuilds context (same builder as advice)
- uses either:
    (A) frontend-provided history (payload.history), OR
    (B) server-side DB history (if store_history=True)
- pulls RAG chunks from FAISS (optional)
- calls LLM (stub) OR fallback
- optionally stores user+assistant messages

Notes:
- store_history=True means backend is the source of truth for chat_messages.
- If frontend sends history, we prefer it (more predictable UI).

TODO (Darsh):
- When LLM is real, enforce JSON-only.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import User, ChatMessage
from app.services.llm_service import call_llm_json
from app.services.advice_service import _build_context_summary

from app.rag.retriever import retrieve, to_chat_sources


def _literacy_prompt_rules(literacy: int) -> str:
    literacy = max(1, min(5, int(literacy or 3)))
    if literacy <= 2:
        return (
            "- Use plain English and define any financial term immediately.\n"
            "- Keep the answer structured and concrete.\n"
            "- Prefer short steps over dense explanation.\n"
        )
    if literacy >= 4:
        return (
            "- The user can handle more detailed reasoning.\n"
            "- You may use moderate technical financial language where it genuinely helps.\n"
            "- Explain why your recommendation follows from their numbers.\n"
        )
    return (
        "- Keep the answer clear, practical, and moderately detailed.\n"
        "- Use only the financial terminology needed for the point.\n"
    )


def chat_reply(
    db: Session,
    *,
    user: User,
    message: str,
    history: list | None = None,
    store_history: bool = True,
) -> dict:
    ctx = _build_context_summary(db, user=user)
    literacy = int(ctx.get("literacy_score", 3) or 3)

    # Prefer frontend-provided history if present
    used_history: list[dict] = []
    if history:
        # history items may be pydantic objects or dicts
        for h in history:
            if hasattr(h, "role") and hasattr(h, "content"):
                used_history.append({"role": h.role, "content": h.content})
            elif isinstance(h, dict):
                used_history.append({"role": h.get("role"), "content": h.get("content")})

    # Otherwise fall back to server-side DB history (optional)
    if not used_history and store_history:
        rows = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(12)
            .all()
        )
        rows = list(reversed(rows))
        used_history = [{"role": r.role, "content": r.content} for r in rows]

    # RAG retrieval (optional)
    rag_chunks = retrieve(message, top_k=4)
    rag_sources = to_chat_sources(rag_chunks)

    rag_text_block = ""
    if rag_chunks:
        rag_text_block = "\n\n".join([f"[{c.source} | {c.chunk_id}] {c.text}" for c in rag_chunks])

    system = (
        "You are FinLit, a friendly and knowledgeable personal finance assistant.\n"
        "Return JSON only. Keys: reply (string), confidence (float 0..1).\n"
        "Rules:\n"
        "- Give a thorough, helpful, and personalized reply using the user's actual numbers.\n"
        "- Reference specific figures from their profile (income, savings, expenses) where relevant.\n"
        "- Use the RAG snippets as supporting context where applicable.\n"
        f"- User literacy_score is {literacy}/5.\n"
        f"{_literacy_prompt_rules(literacy)}"
        "- Use bullet points or numbered steps inside the reply string where helpful.\n"
        "- Do not truncate your response - complete every sentence fully.\n"
        "- If the user has no profile yet, encourage them to fill it in first.\n"
    )

    user_msg = (
        f"Context (DB): {ctx}\n\n"
        f"Recent chat: {used_history}\n\n"
        f"RAG snippets:\n{rag_text_block if rag_text_block else '(none)'}\n\n"
        f"User: {message}"
    )

    llm = call_llm_json(system=system, user=user_msg)

    if not llm:
        # fallback reply
        if not ctx.get("profile"):
            reply = (
                "I can help - but first fill in your income + expenses (profile). "
                "Then I can do breakdowns, stress tests, and goal plans."
            )
        else:
            reply = (
                "Got it. Start with /spending/breakdown, then run a stress test after any changes "
                "to see the impact clearly."
            )
        llm = {"reply": reply, "confidence": 0.6}

    reply_text = str(llm.get("reply", "")).strip()

    # store messages (optional)
    if store_history:
        db.add(ChatMessage(user_id=user.id, role="user", content=message, sources=[]))
        db.add(ChatMessage(user_id=user.id, role="assistant", content=reply_text, sources=rag_sources))
        db.commit()

    # IMPORTANT: return schema-consistent keys
    return {"response": reply_text, "sources": rag_sources}


def get_chat_history(db: Session, *, user: User, limit: int = 30) -> list[dict]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    rows = list(reversed(rows))

    out = []
    for r in rows:
        out.append(
            {
                "role": r.role,
                "content": r.content,
                "sources": r.sources or [],
                "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else "",
            }
        )
    return out


def clear_chat_history(db: Session, *, user: User) -> int:
    """
    Delete all persisted chat messages for the user.
    Returns number of deleted rows.
    """
    deleted = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
    db.commit()
    return int(deleted or 0)
