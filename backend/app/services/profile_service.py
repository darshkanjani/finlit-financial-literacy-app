"""

Profile (onboarding form) logic.

Goals of this service:
- One profile per user (upsert behaviour)
- Store the final validated numbers in financial_profiles
- Optionally compute and store literacy_score in users table

New fields added:
- age_band (broad, optional)
- employment_status (broad, optional)
- occupation_category (broad, optional)
- dependents_count (int, default 0)
- savings_buffer (float, default 0)

Why these matter:
- stress test becomes meaningful if we have savings_buffer
- advice/chat can be slightly more relevant (student vs employed, dependents, etc.)
- keep it non-invasive: no exact DOB, no employer name

What the frontend wants:
- POST /profile with the form body (create-or-overwrite for now)
- GET /profile returns what’s saved + computed totals
- frontend can ignore new fields until ready; backend accepts them anyway

Rules (keep simple):
- monthly_income must be > 0
- all expense fields must be >= 0
- dependents_count >= 0
- savings_buffer >= 0
- literacy_score: if literacy_answers provided, map to 1..5

TODO (Ethan):
- If you want partial update later, make PATCH/PUT + separate ProfileUpdate schema.
- For now, POST acts like “create or overwrite” (but we keep old values if payload omits optional fields).
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import FinancialProfile, User, UserPreference


_EXPENSE_FIELDS = [
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

# Optional context fields (not required for the app to work).
_CONTEXT_FIELDS = [
    "age_band",
    "employment_status",
    "occupation_category",
]

# Optional: tighten these later. For now we store whatever, but we normalise.
_ALLOWED_AGE_BANDS = {"18-24", "25-34", "35-44", "45-54", "55+"}
_ALLOWED_EMPLOYMENT = {"student", "employed", "self_employed", "unemployed"}
_ALLOWED_OCCUPATION = {"tech", "finance", "retail", "healthcare", "other"}
_MAX_MONETARY_FIELD = 1_000_000.0
_ALLOWED_CURRENCY_CODES = {"GBP", "USD", "EUR", "CAD", "AUD", "INR", "JPY", "AED"}
_DEFAULT_CURRENCY_CODE = "GBP"


def _clean_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    v = str(value).strip()
    return v if v else None


def _clean_optional_enum(value: str | None, allowed: set[str]) -> str | None:
    """
    Keeps values neat and avoids random junk in DB.
    If frontend sends something we don't recognize, just store None.
    """
    v = _clean_optional_str(value)
    if v is None:
        return None
    v = v.lower()
    return v if v in allowed else None


def _clean_currency_code(value: str | None) -> str:
    v = _clean_optional_str(value)
    if not v:
        return _DEFAULT_CURRENCY_CODE
    upper = v.upper()
    return upper if upper in _ALLOWED_CURRENCY_CODES else _DEFAULT_CURRENCY_CODE


def _get_or_create_preferences(db: Session, *, user_id: str) -> UserPreference:
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if prefs:
        return prefs
    prefs = UserPreference(user_id=user_id, currency_code=_DEFAULT_CURRENCY_CODE)
    db.add(prefs)
    return prefs


def _compute_literacy_score(literacy_answers: list[int] | None) -> int | None:
    """
    Very basic scoring:
    - answers assumed 1..5
    - score = rounded average, clamped 1..5
    If we want something more meaningful later, we can change here only.
    """
    if not literacy_answers:
        return None

    cleaned = [a for a in literacy_answers if isinstance(a, int)]
    if not cleaned:
        return None

    avg = sum(cleaned) / len(cleaned)
    score = int(round(avg))
    return max(1, min(5, score))


def _resolve_literacy_score(payload_dict: dict, current_score: int) -> int:
    """
    Prefer explicit manual score, otherwise estimate from answers, otherwise keep current.
    """
    manual_score = payload_dict.get("manual_literacy_score")
    if manual_score is not None:
        return max(1, min(5, int(manual_score)))

    estimated = _compute_literacy_score(payload_dict.get("literacy_answers"))
    if estimated is not None:
        return estimated

    return max(1, min(5, int(current_score or 3)))


def upsert_profile(db: Session, *, user: User, payload_dict: dict) -> FinancialProfile:
    """
    Create or update the user's profile.
    One row per user.

    payload_dict should match ProfileIn fields.
    """
    income = payload_dict.get("monthly_income")
    if income is None or income <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="monthly_income must be > 0")
    if float(income) > _MAX_MONETARY_FIELD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"monthly_income looks too high (max allowed is {_MAX_MONETARY_FIELD:,.0f})",
        )

    # validate expenses are not negative
    expense_values: list[float] = []
    for f in _EXPENSE_FIELDS:
        val = payload_dict.get(f, 0)
        if val is None:
            val = 0
        if val < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{f} must be >= 0")
        if float(val) > _MAX_MONETARY_FIELD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{f} looks too high (max allowed is {_MAX_MONETARY_FIELD:,.0f})",
            )
        expense_values.append(float(val))

    # validate new numeric fields
    dependents = payload_dict.get("dependents_count", 0)
    if dependents is None:
        dependents = 0
    if int(dependents) < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="dependents_count must be >= 0")

    buffer_amt = payload_dict.get("savings_buffer", 0)
    if buffer_amt is None:
        buffer_amt = 0
    if float(buffer_amt) < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="savings_buffer must be >= 0")
    if float(buffer_amt) > _MAX_MONETARY_FIELD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"savings_buffer looks too high (max allowed is {_MAX_MONETARY_FIELD:,.0f})",
        )

    # Typo guardrail: allow deficit budgets, but block extreme outliers likely caused by accidental extra zeros.
    total_expenses = sum(expense_values)
    if total_expenses > float(income) * 20 and total_expenses > 50_000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Total monthly expenses look unusually high compared to your income. "
                "Please check for input typos (for example extra zeros)."
            ),
        )

    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    prefs = _get_or_create_preferences(db, user_id=user.id)

    is_new_profile = profile is None  # Track first-time creation
    if is_new_profile:
        profile = FinancialProfile(user_id=user.id)
        db.add(profile)

    # copy core numeric fields
    profile.monthly_income = float(income)
    for f in _EXPENSE_FIELDS:
        setattr(profile, f, float(payload_dict.get(f, 0) or 0))

    # copy new context fields (optional)
    # We normalise / clamp them so DB doesn't fill with random strings.
    # If you want to be looser, replace _clean_optional_enum with _clean_optional_str.
    if "age_band" in payload_dict:
        profile.age_band = _clean_optional_enum(payload_dict.get("age_band"), _ALLOWED_AGE_BANDS)
    if "employment_status" in payload_dict:
        profile.employment_status = _clean_optional_enum(payload_dict.get("employment_status"), _ALLOWED_EMPLOYMENT)
    if "occupation_category" in payload_dict:
        profile.occupation_category = _clean_optional_enum(payload_dict.get("occupation_category"), _ALLOWED_OCCUPATION)

    # numeric context fields (always safe defaults)
    profile.dependents_count = int(dependents)
    profile.savings_buffer = float(buffer_amt)

    # literacy scoring (store on users table)
    user.literacy_score = _resolve_literacy_score(payload_dict, int(getattr(user, "literacy_score", 3) or 3))

    prefs.currency_code = _clean_currency_code(payload_dict.get("currency_code"))

    db.commit()
    db.refresh(profile)

    # On first profile creation: auto-run all 3 stress tests then generate welcome advice.
    # This ensures the dashboard is fully populated from day 1.
    if is_new_profile:
        _run_initial_analysis(db, user=user, profile=profile)

    return profile


def _run_initial_analysis(db: Session, *, user: User, profile: FinancialProfile) -> None:
    """
    Runs on first profile creation only.
    Auto-runs all 3 stress test scenarios and generates welcome advice.
    Errors are caught silently so they never block the profile save.
    """
    from app.services.stress_service import run_and_store_stress_test
    from app.services.advice_service import generate_welcome_advice

    # Default emergency cost: 1 month of income (a realistic one-off shock)
    emergency_amount = float(profile.monthly_income)

    scenarios = [
        ("job_loss", {}),
        ("emergency", {"amount": emergency_amount}),
        ("promotion", {}),
    ]

    for scenario_type, params in scenarios:
        try:
            run_and_store_stress_test(db, user=user, scenario_type=scenario_type, params=params)
        except Exception:
            pass  # Don't block profile creation if a scenario fails

    try:
        generate_welcome_advice(db, user=user)
    except Exception:
        pass  # Don't block profile creation if advice generation fails


def get_profile(db: Session, *, user: User) -> FinancialProfile:
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


def get_user_currency_code(db: Session, *, user_id: str) -> str:
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not prefs:
        return _DEFAULT_CURRENCY_CODE
    return _clean_currency_code(getattr(prefs, "currency_code", _DEFAULT_CURRENCY_CODE))


def profile_to_out(*, db: Session, profile: FinancialProfile, user: User) -> dict:
    """
    Convert ORM to ProfileOut dict.
    Keep this as the single mapping place so we don’t duplicate logic in endpoints.
    """
    total_expenses = sum(float(getattr(profile, f) or 0) for f in _EXPENSE_FIELDS)
    savings_potential = float(profile.monthly_income) - total_expenses

    currency_code = get_user_currency_code(db, user_id=user.id)

    return {
        "profile_id": str(profile.id),
        "monthly_income": float(profile.monthly_income),
        "currency_code": currency_code,

        # new context echoed back (frontend can display later)
        "age_band": getattr(profile, "age_band", None),
        "employment_status": getattr(profile, "employment_status", None),
        "occupation_category": getattr(profile, "occupation_category", None),
        "dependents_count": int(getattr(profile, "dependents_count", 0) or 0),
        "savings_buffer": float(getattr(profile, "savings_buffer", 0.0) or 0.0),

        # existing fields
        "rent": float(profile.rent),
        "bills": float(profile.bills),
        "subscriptions": float(profile.subscriptions),
        "loan_repayments": float(profile.loan_repayments),
        "groceries": float(profile.groceries),
        "transport": float(profile.transport),
        "entertainment": float(profile.entertainment),
        "eating_out": float(profile.eating_out),
        "clothing": float(profile.clothing),
        "health": float(profile.health),
        "other": float(profile.other),

        "total_expenses": float(total_expenses),
        "savings_potential": float(savings_potential),

        "literacy_score": int(user.literacy_score or 3),
    }
