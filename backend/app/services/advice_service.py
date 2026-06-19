"""

Advice generation service.

What it does:
- rebuilds context from DB (profile + goals + latest stress + literacy_score)
- pulls RAG chunks from FAISS (optional, if index exists)
- calls LLM (still stubbed) OR returns heuristic advice
- stores AdviceHistory

Notes:
- RAG is optional: if index files don't exist, retrieve() just returns [] and we continue.
- We keep the sources list even in fallback, so UI is consistent.

TODO (Darsh):
- When you wire a real LLM provider, enforce JSON-only responses.
- If literacy_score is low, keep advice short + avoid jargon.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import User, FinancialProfile, Goal, StressTestResult, AdviceHistory
from app.services.llm_service import call_llm_json

# FAISS RAG (optional)
from app.rag.retriever import retrieve, to_advice_sources

PROFILE_FIELDS = [
    "rent", "bills", "subscriptions", "loan_repayments",
    "groceries", "transport", "entertainment", "eating_out",
    "clothing", "health", "other",
]

QUESTION_MARKER = "__user_question__:"


def _literacy_prompt_rules(literacy: int) -> str:
    literacy = max(1, min(5, int(literacy or 3)))
    if literacy <= 2:
        return (
            "- Use plain English and short sentences.\n"
            "- Avoid jargon unless you define it immediately.\n"
            "- Give 2-3 concrete actions, not a long essay.\n"
        )
    if literacy >= 4:
        return (
            "- The user can handle moderate technical detail.\n"
            "- You may use budgeting/stress-testing terminology, but stay concrete.\n"
            "- Explain tradeoffs and reasoning, not just the final answer.\n"
        )
    return (
        "- Keep explanations clear and practical.\n"
        "- Use light financial terminology only where useful.\n"
        "- Balance brevity with enough reasoning to be actionable.\n"
    )


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


def _attach_question_to_sources(message: str, sources: list[dict]) -> list[dict]:
    prompt = (message or "").strip()
    if not prompt:
        return sources
    return [{"title": f"{QUESTION_MARKER}{prompt}", "url": None}] + list(sources or [])


def _extract_question_from_sources(sources: list[dict]) -> tuple[str | None, list[dict]]:
    question: str | None = None
    cleaned: list[dict] = []
    for s in sources or []:
        title = str((s or {}).get("title", ""))
        if title.startswith(QUESTION_MARKER):
            if question is None:
                question = title.replace(QUESTION_MARKER, "", 1).strip() or None
            continue
        cleaned.append(s)
    return question, cleaned


def _build_context_summary(db: Session, *, user: User) -> dict:
    """
    Keep this compact.
    LLM gets enough to be grounded and consistent.
    """
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()

    goals = (
        db.query(Goal)
        .filter(Goal.user_id == user.id)
        .order_by(Goal.created_at.desc())
        .limit(5)
        .all()
    )

    latest_stress = (
        db.query(StressTestResult)
        .filter(StressTestResult.user_id == user.id)
        .order_by(StressTestResult.created_at.desc())
        .first()
    )
    all_stress = db.query(StressTestResult).filter(StressTestResult.user_id == user.id).all()

    profile_summary = None
    if profile:
        expenses = {f: float(getattr(profile, f) or 0) for f in PROFILE_FIELDS}
        total_expenses = round(sum(expenses.values()), 2)
        income = float(profile.monthly_income)
        savings = round(income - total_expenses, 2)

        profile_summary = {
            "monthly_income": income,
            "expenses": expenses,
            "total_expenses": total_expenses,
            "savings_potential": savings,

            # optional context fields (only if you added columns)
            "savings_buffer": float(getattr(profile, "savings_buffer", 0.0) or 0.0),
            "employment_status": getattr(profile, "employment_status", None),
            "dependents_count": int(getattr(profile, "dependents_count", 0) or 0),
            "age_band": getattr(profile, "age_band", None),
            "occupation_category": getattr(profile, "occupation_category", None),
        }

    goals_summary = [
        {
            "goal_name": g.goal_name,
            "target_amount": float(g.target_amount),
            "current_amount": float(g.current_amount),
            "target_date": getattr(g, "target_date", None),
            "status": g.status,
        }
        for g in goals
    ]

    stress_summary = None
    if latest_stress:
        stress_summary = {
            "scenario_type": latest_stress.scenario_type,
            "months_until_broke": latest_stress.months_until_broke,
            "resilience_score": float(latest_stress.resilience_score or 0),
        }

    stress_by_scenario = []
    stress_overall = None
    if all_stress:
        latest_rows = _latest_stress_by_scenario(all_stress)
        for row in latest_rows:
            stress_by_scenario.append(
                {
                    "scenario_type": row.scenario_type,
                    "resilience_score": float(row.resilience_score or 0),
                    "months_until_broke": row.months_until_broke,
                    "created_at": row.created_at.isoformat() if getattr(row, "created_at", None) else None,
                }
            )
        scores = [float(r.resilience_score or 0) for r in latest_rows]
        if scores:
            avg = sum(scores) / len(scores)
            weakest = min(latest_rows, key=lambda r: float(r.resilience_score or 0))
            stress_overall = {
                "overall_resilience_score": round(avg, 2),
                "weakest_scenario": getattr(weakest, "scenario_type", None),
            }

    return {
        "literacy_score": int(getattr(user, "literacy_score", 3) or 3),
        "profile": profile_summary,
        "goals": goals_summary,
        "stress_overall": stress_overall,
        "stress_by_scenario": stress_by_scenario,
        "latest_stress": stress_summary,
    }


def generate_advice(db: Session, *, user: User, message: str) -> dict:
    ctx = _build_context_summary(db, user=user)
    literacy = int(ctx.get("literacy_score", 3))

    # RAG: grab chunks relevant to the message (safe if index missing)
    rag_chunks = retrieve(message, top_k=4)
    rag_sources = to_advice_sources(rag_chunks)  # MUST output AdviceSource-shaped dicts

    rag_text_block = ""
    if rag_chunks:
        rag_text_block = "\n\n".join([f"[{c.source} | {c.chunk_id}] {c.text}" for c in rag_chunks])

    # IMPORTANT: Our API schema wants "advice", but LLM prompt can still return advice_text.
    # We'll normalize whatever comes back.
    system = (
        "You are FinLit, a financial coaching assistant.\n"
        "Return JSON only.\n"
        "Keys: advice_text (string), action_items (list of strings), confidence (0..1).\n"
        "Rules:\n"
        "- Ground advice in the user's actual profile numbers.\n"
        "- If the user profile is missing, ask them to complete it.\n"
        "- If RAG snippets are provided, use them as supporting context.\n"
        f"- User literacy_score is {literacy}/5.\n"
        f"{_literacy_prompt_rules(literacy)}"
    )

    user_msg = (
        f"User message: {message}\n\n"
        f"User context (from DB): {ctx}\n\n"
        f"RAG snippets (optional):\n{rag_text_block if rag_text_block else '(none)'}\n"
    )

    llm = call_llm_json(system=system, user=user_msg)

    if not llm:
        # fallback: deterministic advice, but still include rag_sources if any
        if not ctx["profile"]:
            advice_text = (
                "I can help, but I need your income + monthly expenses first. "
                "Fill in the onboarding form so I can calculate your savings rate and run stress tests."
            )
            action_items = ["Complete your profile (income + monthly expenses)."]
            confidence = 0.55
        else:
            p = ctx["profile"]
            income = float(p["monthly_income"])
            total_expenses = float(p["total_expenses"])
            savings = round(income - total_expenses, 2)

            if literacy <= 2:
                advice_text = (
                    f"You have about £{savings}/month left after expenses. "
                    "To improve fast, cut small wants (subscriptions/eating out)."
                )
                action_items = [
                    "Cancel 1 unused subscription.",
                    "Set an eating-out limit for the week.",
                ]
            else:
                advice_text = (
                    f"Based on your numbers you’ve got about £{savings}/month left after expenses. "
                    "Fast wins are usually subscriptions, eating out, and entertainment."
                )
                action_items = [
                    "Cancel unused subscriptions.",
                    "Set a weekly eating-out budget.",
                    "Re-run stress tests after changes to see resilience improve.",
                ]

            confidence = 0.65

        advice_text = str(advice_text)
        llm = {"advice_text": advice_text, "action_items": action_items, "confidence": confidence}

    # Normalize + enforce sources we control (RAG metadata)
    advice_text = str(llm.get("advice_text", "")).strip()
    action_items = llm.get("action_items", []) or []
    confidence = float(llm.get("confidence", 0.6))

    stored_sources = _attach_question_to_sources(message, rag_sources)

    # Persist
    row = AdviceHistory(
        user_id=user.id,
        advice_text=advice_text,
        action_items=action_items,
        sources=stored_sources,
        literacy_level_used=literacy,
        confidence=confidence,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # IMPORTANT: return schema-consistent keys
    question, visible_sources = _extract_question_from_sources(row.sources or [])

    return {
        "id": str(row.id),
        "question": question,
        "advice": row.advice_text,
        "action_items": row.action_items or [],
        "sources": visible_sources,
        "literacy_level_used": int(row.literacy_level_used or literacy),
        "confidence": float(row.confidence or 0.0),
        "created_at": row.created_at.isoformat() if getattr(row, "created_at", None) else None,
    }


def generate_welcome_advice(db: Session, *, user: User) -> AdviceHistory:
    """
    Generate contextual welcome advice after first profile creation.

    By the time this runs we always have a profile and all 3 stress test results
    (auto-run just before in _run_initial_analysis). So advice uses real numbers,
    not generic placeholders.

    Adapts language to literacy_score (1=simple, 5=detailed).
    """
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    literacy = int(getattr(user, "literacy_score", 3) or 3)

    # Compute basic numbers from profile
    expenses = {f: float(getattr(profile, f) or 0) for f in PROFILE_FIELDS}
    total_expenses = round(sum(expenses.values()), 2)
    income = float(profile.monthly_income)
    monthly_savings = round(income - total_expenses, 2)
    savings_rate = round((monthly_savings / income) * 100, 1) if income > 0 else 0

    # Pull job_loss result - most important scenario for grounding advice
    job_loss_result = (
        db.query(StressTestResult)
        .filter(StressTestResult.user_id == user.id, StressTestResult.scenario_type == "job_loss")
        .order_by(StressTestResult.created_at.desc())
        .first()
    )

    months_until_broke = getattr(job_loss_result, "months_until_broke", None) if job_loss_result else None
    resilience_score = float(getattr(job_loss_result, "resilience_score", 0) or 0) if job_loss_result else 0.0

    # Resilience rating string
    if resilience_score < 3:
        resilience_label = "low"
    elif resilience_score < 5:
        resilience_label = "moderate"
    elif resilience_score < 7:
        resilience_label = "good"
    else:
        resilience_label = "excellent"

    if literacy <= 2:
        # Short, plain English - no jargon
        if months_until_broke is not None and months_until_broke < 3:
            advice_text = (
                f"Welcome! You earn £{income:.0f}/month and spend £{total_expenses:.0f}/month. "
                f"If you lost your job today, your money would run out in about {months_until_broke} month(s). "
                f"That's risky. Start saving more as soon as you can."
            )
        else:
            advice_text = (
                f"Welcome! You earn £{income:.0f}/month and spend £{total_expenses:.0f}/month, "
                f"leaving £{monthly_savings:.0f} spare each month. "
                f"If you lost your job, you'd last about {months_until_broke} month(s). "
                f"A good next step is to set a savings goal."
            )
        action_items = [
            "Set a savings goal - an emergency fund is a great start",
            "Try to save at least 10% of your income each month",
            "Use the Chat tab to ask me anything",
        ]

    else:
        # Standard language - more detail, references all 3 scenarios
        broke_str = f"{months_until_broke} month(s)" if months_until_broke is not None else "an unknown period"
        advice_text = (
            f"Welcome to FinLit! Here's your financial snapshot based on your profile:\n\n"
            f"• Monthly income: £{income:.2f}\n"
            f"• Monthly expenses: £{total_expenses:.2f}\n"
            f"• Monthly savings potential: £{monthly_savings:.2f} ({savings_rate}% savings rate)\n"
            f"• Job loss resilience: {broke_str} until funds run out "
            f"(score: {resilience_score:.1f}/10 - {resilience_label})\n\n"
            f"We've already run all 3 stress tests (job loss, emergency, promotion) - "
            f"check the Stress Tests tab for the full breakdown. "
            f"Your immediate next step is to set a financial goal. "
            f"An emergency fund covering 3-6 months of expenses is recommended."
        )
        action_items = [
            f"Create an emergency fund goal (target: £{round(total_expenses * 3):.0f}-£{round(total_expenses * 6):.0f})",
            "Review your stress test results in the Stress Tests tab",
            "Use 'Get Advice' for personalised recommendations anytime",
            "Use the Chat tab for specific financial questions",
        ]

    row = AdviceHistory(
        user_id=user.id,
        advice_text=advice_text,
        action_items=action_items,
        sources=[],
        literacy_level_used=literacy,
        confidence=0.9,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_advice_history(db: Session, *, user: User) -> list[dict]:
    rows = (
        db.query(AdviceHistory)
        .filter(AdviceHistory.user_id == user.id)
        .order_by(AdviceHistory.created_at.desc())
        .limit(20)
        .all()
    )

    out = []
    for r in rows:
        question, visible_sources = _extract_question_from_sources(r.sources or [])
        out.append(
            {
                "id": str(r.id),
                "question": question,
                "advice": r.advice_text,
                "action_items": r.action_items or [],
                "sources": visible_sources,
                "confidence": float(r.confidence or 0.0),
                "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else "",
            }
        )
    return out


def clear_advice_history(db: Session, *, user: User) -> int:
    """
    Delete all saved advice rows for the user.
    Returns number of deleted rows.
    """
    deleted = db.query(AdviceHistory).filter(AdviceHistory.user_id == user.id).delete()
    db.commit()
    return int(deleted or 0)
