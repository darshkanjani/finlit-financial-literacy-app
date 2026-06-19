"""

Stress test service:
- loads user profile from DB
- builds ProfileSnapshot
- runs stress_engine simulation (month-by-month)
- stores StressTestResult row

Option 1 (deterministic):
- params supported: income_replacement, cutback_percent, months/horizon_months, amount/spread_months, etc.
- uses savings_buffer as starting savings

Option 2 (ML assist, still safe):
- if cutback_percent isn't provided, try ML model prediction
- if ML model isn't available, fall back to engine's internal defaults (rule-based)

Notes:
- This service orchestrates. The engine does the maths.
- No DB writes except inserting the StressTestResult row.
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import FinancialProfile, StressTestResult, User
from app.ml.stress_engine import ProfileSnapshot, run_scenario

from app.ml.cutback_model import (
    CutbackFeatures,
    load_model,
    predict_cutback_percent,
    MODEL_PATH_DEFAULT,
    # train_and_save_model,  # optional (see comment below)
)

# Keep these aligned with FinancialProfile columns
EXPENSE_FIELDS = [
    "rent",
    "bills",
    "subscriptions",
    "loan_repayments",
    "groceries",
    "transport",
    "entertainment",
    "eating_out",
    "clothing",
    "health",
    "other",
]


# -----------------------
# Internal helpers
# -----------------------

def _get_profile_or_400(db: Session, user: User) -> FinancialProfile:
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your profile first before running stress tests.",
        )
    return profile


def _snapshot_from_profile(profile: FinancialProfile) -> ProfileSnapshot:
    """
    Map DB profile -> engine snapshot.
    Keep mapping dead simple and explicit.
    """
    return ProfileSnapshot(
        monthly_income=float(profile.monthly_income),

        rent=float(profile.rent or 0),
        bills=float(profile.bills or 0),
        subscriptions=float(profile.subscriptions or 0),
        loan_repayments=float(profile.loan_repayments or 0),
        groceries=float(profile.groceries or 0),
        transport=float(profile.transport or 0),
        entertainment=float(profile.entertainment or 0),
        eating_out=float(profile.eating_out or 0),
        clothing=float(profile.clothing or 0),
        health=float(profile.health or 0),
        other=float(profile.other or 0),

        # Context fields (optional columns; getattr makes it safe even if DB not migrated yet)
        savings_buffer=float(getattr(profile, "savings_buffer", 0.0) or 0.0),
        employment_status=getattr(profile, "employment_status", None),
        dependents_count=int(getattr(profile, "dependents_count", 0) or 0),
        age_band=getattr(profile, "age_band", None),
        occupation_category=getattr(profile, "occupation_category", None),
    )


def _ratios_for_ml(profile: FinancialProfile) -> tuple[float, float, float]:
    """
    Basic engineered features for the cutback model.
    Ratios are stable and explainable for coursework.
    """
    income = float(profile.monthly_income or 0.0)
    if income <= 0:
        return 0.0, 0.0, 0.0

    needs = (
        float(profile.rent or 0)
        + float(profile.bills or 0)
        + float(profile.groceries or 0)
        + float(profile.transport or 0)
        + float(profile.health or 0)
        + float(profile.loan_repayments or 0)
    )
    wants = (
        float(profile.subscriptions or 0)
        + float(profile.entertainment or 0)
        + float(profile.eating_out or 0)
        + float(profile.clothing or 0)
        + float(profile.other or 0)
    )
    debt = float(profile.loan_repayments or 0)

    return needs / income, wants / income, debt / income


def _maybe_fill_cutback_with_ml(*, user: User, profile: FinancialProfile, params: dict) -> dict:
    """
    Option 2:
    If params doesn't include cutback_percent, try:
    - load model
    - predict cutback_percent
    - attach to params

    IMPORTANT: don't auto-train during API calls by default.
    (Auto-training can be slow and is weird for a demo.)
    If model not found -> do nothing, engine will use rule-based default.
    """
    if params.get("cutback_percent") is not None:
        return params

    model = load_model(MODEL_PATH_DEFAULT)
    if model is None:
        # If you REALLY want auto-training in dev, uncomment:
        # train_and_save_model(MODEL_PATH_DEFAULT, n=4000)
        # model = load_model(MODEL_PATH_DEFAULT)
        return params

    needs_ratio, wants_ratio, debt_ratio = _ratios_for_ml(profile)

    pred = predict_cutback_percent(
        model,
        CutbackFeatures(
            needs_ratio=needs_ratio,
            wants_ratio=wants_ratio,
            debt_ratio=debt_ratio,
            income=float(profile.monthly_income),
            dependents_count=int(getattr(profile, "dependents_count", 0) or 0),
            employment_status=getattr(profile, "employment_status", None),
            literacy_score=int(getattr(user, "literacy_score", 3) or 3),
        ),
    )

    if pred is not None:
        params["cutback_percent"] = float(round(pred, 3))
        params.setdefault("ml_used", True)  # for transparency/debug/demo

    return params


def _normalize_param_aliases(params: dict) -> dict:
    """
    Accept frontend/Swagger-friendly aliases without breaking engine contract.

    Engine expects:
      - horizon_months

    Frontend/Swagger might send:
      - months

    We normalize here so BOTH work.
    """
    if "months" in params and "horizon_months" not in params:
        params["horizon_months"] = params["months"]
    return params


def _derive_month_broke_from_projections(monthly_projections: list) -> int | None:
    """
    We don't store month_broke in DB (no schema change needed).
    Derive it from projections at response time.

    month_broke = first month where savings_remaining <= 0
    """
    for p in monthly_projections or []:
        try:
            if float(p.get("savings_remaining", 1)) <= 0:
                return int(p.get("month"))
        except Exception:
            continue
    return None


# -----------------------
# Public service API (used by endpoints)
# -----------------------

def run_and_store_stress_test(
    db: Session,
    *,
    user: User,
    scenario_type: str,
    params: dict | None = None,
) -> StressTestResult:
    """
    Main entrypoint:
    - load profile
    - create snapshot
    - normalize params
    - apply ML assist (only if relevant)
    - run engine
    - store StressTestResult row
    """
    params = _normalize_param_aliases(params or {})
    scenario_norm = (scenario_type or "").lower().strip()

    profile = _get_profile_or_400(db, user)
    snapshot = _snapshot_from_profile(profile)

    # Option 2 ML assist: only for job_loss, only if cutback_percent not provided
    if scenario_norm == "job_loss":
        params = _maybe_fill_cutback_with_ml(user=user, profile=profile, params=params)

    try:
        result = run_scenario(snapshot, scenario_type=scenario_type, params=params)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    params_to_store = dict(params or {})
    if result.get("score_breakdown"):
        params_to_store["score_breakdown"] = result["score_breakdown"]
    if result.get("score_meta"):
        params_to_store["score_meta"] = result["score_meta"]

    row = StressTestResult(
        user_id=user.id,
        scenario_type=scenario_type,
        params=params_to_store,
        monthly_projections=result.get("monthly_projections", []),
        months_until_broke=result.get("months_until_broke"),
        resilience_score=float(result.get("resilience_score", 0.0)),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def stress_row_to_out(row: StressTestResult) -> dict:
    """
    Single mapping place.
    Endpoint can just return this dict.

    Note:
    - months_until_broke = FULL months survived (0..horizon), per engine semantics
    - month_broke (new) = first month where savings_remaining <= 0 (derived from projections)
    """
    projections = row.monthly_projections or []
    month_broke = _derive_month_broke_from_projections(projections)

    return {
        "id": str(row.id),
        "scenario_type": row.scenario_type,
        "params": row.params or {},
        "monthly_projections": projections,
        "months_until_broke": row.months_until_broke,
        "month_broke": month_broke,
        "resilience_score": float(row.resilience_score or 0.0),
        "created_at": row.created_at.isoformat() if getattr(row, "created_at", None) else None,
    }


# --- Compatibility wrappers (so your endpoints can stay as I wrote earlier) ---

def run_stress_test(db: Session, *, user: User, scenario_type: str, params: dict) -> dict:
    """
    Wrapper returning dict (not ORM row).
    Keeps endpoint code simple.
    """
    row = run_and_store_stress_test(db, user=user, scenario_type=scenario_type, params=params)
    return stress_row_to_out(row)


def list_stress_history(db: Session, *, user: User, limit: int = 15) -> list[dict]:
    rows = (
        db.query(StressTestResult)
        .filter(StressTestResult.user_id == user.id)
        .order_by(StressTestResult.created_at.desc())
        .limit(limit)
        .all()
    )
    return [stress_row_to_out(r) for r in rows]


def resilience_summary(db: Session, *, user: User) -> dict:
    rows = db.query(StressTestResult).filter(StressTestResult.user_id == user.id).all()
    if not rows:
        return {"overall_score": 0.0, "rating": "none", "weakest_scenario": None}

    latest_by_scenario: dict[str, StressTestResult] = {}
    for row in rows:
        scenario = getattr(row, "scenario_type", "") or ""
        existing = latest_by_scenario.get(scenario)
        if existing is None:
            latest_by_scenario[scenario] = row
            continue
        if getattr(row, "created_at", None) and getattr(existing, "created_at", None):
            if row.created_at > existing.created_at:
                latest_by_scenario[scenario] = row

    latest_rows = list(latest_by_scenario.values()) or rows
    scores = [float(r.resilience_score or 0.0) for r in latest_rows]
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

    weakest = min(latest_rows, key=lambda r: float(r.resilience_score or 0.0))
    return {"overall_score": round(avg, 2), "rating": rating, "weakest_scenario": weakest.scenario_type}
