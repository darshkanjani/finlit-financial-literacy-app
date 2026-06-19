"""

Stress test simulation engine.

This file is PURE logic:
- no DB
- no FastAPI
- no SQLAlchemy

Inputs:
- a ProfileSnapshot (numbers + a couple context fields)
- scenario + params

Outputs:
- dict with monthly_projections, months_until_broke, resilience_score, summary

Design goals (uni project):
- deterministic baseline so it's reliable
- parameterisable so frontend can add sliders
- uses savings_buffer so results actually mean something
- uses simple, explainable assumptions (no black box)

Scenarios:
- job_loss
- promotion
- emergency

Params (all optional, per scenario):
job_loss:
  - income_replacement: float (0..1) default 0.0
  - cutback_percent: float (0..0.9) default derived from profile
  - cutback_start_month: int default 2  (month 1 is "shock month", no cutback)
  - horizon_months: int default 12
  - months: int alias for horizon_months (frontend-friendly)

promotion:
  - income_increase_percent: float default 20
  - lifestyle_inflation_percent: float default 0
  - horizon_months: int default 12
  - months: int alias for horizon_months

emergency:
  - amount: float default 1000
  - spread_months: int default 1 (1 = hits month 1 as lump sum)
  - horizon_months: int default 12
  - months: int alias for horizon_months
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ---------- Profile snapshot ----------

@dataclass
class ProfileSnapshot:
    monthly_income: float

    # expenses (same names as your FinancialProfile columns)
    rent: float = 0
    bills: float = 0
    subscriptions: float = 0
    loan_repayments: float = 0
    groceries: float = 0
    transport: float = 0
    entertainment: float = 0
    eating_out: float = 0
    clothing: float = 0
    health: float = 0
    other: float = 0

    # new: buffer + context
    savings_buffer: float = 0
    employment_status: str | None = None
    dependents_count: int = 0
    age_band: str | None = None
    occupation_category: str | None = None

    def needs_total(self) -> float:
        # Keep your own mapping consistent with spending_service.
        return float(self.rent + self.bills + self.groceries + self.transport + self.health + self.loan_repayments)

    def wants_total(self) -> float:
        return float(self.subscriptions + self.entertainment + self.eating_out + self.clothing + self.other)

    def total_expenses(self) -> float:
        return float(self.needs_total() + self.wants_total())


# ---------- Helpers ----------

def clamp(x: float, lo: float, hi: float) -> float:
    try:
        x = float(x)
    except Exception:
        x = lo
    return max(lo, min(hi, x))


def _default_cutback_percent(profile: ProfileSnapshot) -> float:
    """
    Explainable defaults (Option 1 baseline):
    - base wants cut = 40% after month 1
    - if dependents > 0 => less flexibility => 25%
    - if student/unemployed => already lean => cap at 30%
    """
    base = 0.40
    if (profile.dependents_count or 0) > 0:
        base = 0.25

    status = (profile.employment_status or "").lower()
    if status in {"student", "unemployed"}:
        base = min(base, 0.30)

    return clamp(base, 0.0, 0.9)


def _resilience_score(months_survived: int, horizon_months: int) -> float:
    # simple 0..10 scaling
    return round(min(10.0, (months_survived / max(1, horizon_months)) * 10.0), 2)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _std_dev(values: list[float]) -> float:
    if not values:
        return 0.0
    mu = _mean(values)
    var = sum((v - mu) ** 2 for v in values) / len(values)
    return float(var ** 0.5)


def _composite_resilience(
    *,
    projections: list[dict[str, Any]],
    months_until_broke: int | None,
    horizon_months: int,
    base_income: float,
    base_expenses: float,
) -> dict[str, Any]:
    """
    Composite 0..10 resilience score:
    - survival   40%: full months survived in the horizon
    - buffer     30%: ending savings vs 3 months baseline expenses
    - cashflow   20%: average monthly net margin
    - stability  10%: volatility of monthly net
    """
    horizon = max(1, int(horizon_months))
    income_ref = max(float(base_income or 0.0), 1.0)
    expenses_ref = max(float(base_expenses or 0.0), 1.0)

    months_survived = horizon if months_until_broke is None else max(0, int(months_until_broke))
    survival_score = clamp(10.0 * (months_survived / horizon), 0.0, 10.0)

    end_buffer = float(projections[-1].get("savings_remaining", 0.0)) if projections else 0.0
    target_buffer = max(expenses_ref * 3.0, 1.0)
    buffer_score = clamp(10.0 * (end_buffer / target_buffer), 0.0, 10.0)

    net_series = [float(p.get("net", 0.0)) for p in projections]
    avg_net = _mean(net_series)
    net_margin = avg_net / income_ref
    cashflow_score = clamp(5.0 + 25.0 * net_margin, 0.0, 10.0)

    net_std = _std_dev(net_series)
    volatility_ratio = net_std / income_ref
    stability_score = clamp(10.0 - 20.0 * volatility_ratio, 0.0, 10.0)

    composite = (
        0.40 * survival_score
        + 0.30 * buffer_score
        + 0.20 * cashflow_score
        + 0.10 * stability_score
    )

    return {
        "composite_score": round(composite, 2),
        "breakdown": {
            "survival": round(survival_score, 2),
            "buffer": round(buffer_score, 2),
            "cashflow": round(cashflow_score, 2),
            "stability": round(stability_score, 2),
        },
        "meta": {
            "months_survived": int(months_survived),
            "horizon_months": int(horizon),
            "end_buffer": round(end_buffer, 2),
            "target_buffer": round(target_buffer, 2),
            "avg_net": round(avg_net, 2),
            "net_volatility": round(net_std, 2),
        },
    }


def _month_obj(month: int, income: float, expenses: float, savings_remaining: float, note: str = "") -> dict[str, Any]:
    return {
        "month": int(month),
        "income": round(float(income), 2),
        "expenses": round(float(expenses), 2),
        "net": round(float(income - expenses), 2),
        "savings_remaining": round(float(savings_remaining), 2),
        "note": note,
    }


def _get_horizon_months(params: dict[str, Any], default: int = 12) -> int:
    """
    Frontend-friendly alias support:
    - accepts either horizon_months OR months
    """
    raw = params.get("horizon_months", params.get("months", default))
    try:
        return int(raw)
    except Exception:
        return int(default)


# ---------- Scenario sims ----------

def run_job_loss(
    profile: ProfileSnapshot,
    *,
    horizon_months: int = 12,
    income_replacement: float = 0.0,
    cutback_percent: float | None = None,
    cutback_start_month: int = 2,
) -> dict[str, Any]:
    horizon_months = int(clamp(horizon_months, 1, 36))
    income_replacement = clamp(income_replacement, 0.0, 1.0)
    cutback_start_month = int(clamp(cutback_start_month, 1, horizon_months))

    # decide cutback
    if cutback_percent is None:
        cutback_percent = _default_cutback_percent(profile)
    else:
        cutback_percent = clamp(cutback_percent, 0.0, 0.9)

    savings = float(profile.savings_buffer or 0.0)
    needs = profile.needs_total()
    wants = profile.wants_total()

    projections: list[dict[str, Any]] = []

    # Option A (agreed):
    # months_until_broke = number of FULL months survived (0..horizon)
    # month_broke = first month where savings <= 0 (1..horizon), more intuitive for UI
    months_until_broke: int | None = None
    month_broke: int | None = None

    for m in range(1, horizon_months + 1):
        income = profile.monthly_income * income_replacement

        if m < cutback_start_month:
            # shock months: user hasn't cut back yet
            expenses = needs + wants
            note = "shock month (no cutback yet)"
        else:
            # after shock: cut wants by cutback_percent
            expenses = needs + wants * (1.0 - cutback_percent)
            note = f"cutback applied (wants -{int(cutback_percent*100)}%)"

        savings = savings + (income - expenses)
        projections.append(_month_obj(m, income, expenses, savings, note=note))

        # Broke detection:
        # use <= 0 so hitting exactly zero counts as "broke"
        if month_broke is None and savings <= 0:
            month_broke = m
            months_until_broke = m - 1  # survived up to previous month (0 is valid)

    composite = _composite_resilience(
        projections=projections,
        months_until_broke=months_until_broke,
        horizon_months=horizon_months,
        base_income=float(profile.monthly_income or 0.0),
        base_expenses=float(profile.total_expenses() or 0.0),
    )
    score = float(composite["composite_score"])

    summary = (
        f"Job loss simulation over {horizon_months} months. "
        f"Started with £{round(profile.savings_buffer,2)} buffer. "
        f"Income replacement {int(income_replacement*100)}%. "
        f"After month {cutback_start_month-1}, wants reduced by {int(cutback_percent*100)}%."
    )

    return {
        "scenario_type": "job_loss",
        "monthly_projections": projections,
        "months_until_broke": months_until_broke,
        "month_broke": month_broke,
        "resilience_score": score,
        "score_breakdown": composite["breakdown"],
        "score_meta": composite["meta"],
        "summary": summary,
    }


def run_promotion(
    profile: ProfileSnapshot,
    *,
    horizon_months: int = 12,
    income_increase_percent: float = 20.0,
    lifestyle_inflation_percent: float = 0.0,
) -> dict[str, Any]:
    horizon_months = int(clamp(horizon_months, 1, 36))
    inc = clamp(income_increase_percent, 0.0, 300.0)
    infl = clamp(lifestyle_inflation_percent, 0.0, 200.0)

    base_income = float(profile.monthly_income)
    base_expenses = float(profile.total_expenses())

    new_income = base_income * (1.0 + inc / 100.0)
    new_expenses = base_expenses * (1.0 + infl / 100.0)

    savings = float(profile.savings_buffer or 0.0)
    projections: list[dict[str, Any]] = []

    for m in range(1, horizon_months + 1):
        income = new_income
        expenses = new_expenses
        savings = savings + (income - expenses)
        projections.append(_month_obj(m, income, expenses, savings, note=f"+{inc}% income, +{infl}% expenses"))

    # Promotion now uses the same composite framework as all scenarios.
    composite = _composite_resilience(
        projections=projections,
        months_until_broke=None,
        horizon_months=horizon_months,
        base_income=float(profile.monthly_income or 0.0),
        base_expenses=float(profile.total_expenses() or 0.0),
    )
    score = float(composite["composite_score"])

    summary = (
        f"Promotion simulation over {horizon_months} months. "
        f"Income +{inc}%, expenses +{infl}% (lifestyle inflation)."
    )

    return {
        "scenario_type": "promotion",
        "monthly_projections": projections,
        "months_until_broke": None,
        "month_broke": None,
        "resilience_score": score,
        "score_breakdown": composite["breakdown"],
        "score_meta": composite["meta"],
        "summary": summary,
    }


def run_emergency(
    profile: ProfileSnapshot,
    *,
    horizon_months: int = 12,
    amount: float = 1000.0,
    spread_months: int = 1,
) -> dict[str, Any]:
    horizon_months = int(clamp(horizon_months, 1, 36))
    amount = clamp(amount, 0.0, 1_000_000.0)
    spread_months = int(clamp(spread_months, 1, horizon_months))

    savings = float(profile.savings_buffer or 0.0)
    base_income = float(profile.monthly_income)
    base_expenses = float(profile.total_expenses())

    emergency_monthly = amount / spread_months if spread_months > 0 else amount

    projections: list[dict[str, Any]] = []
    months_until_broke: int | None = None
    month_broke: int | None = None

    for m in range(1, horizon_months + 1):
        extra = emergency_monthly if m <= spread_months else 0.0
        income = base_income
        expenses = base_expenses + extra

        savings = savings + (income - expenses)
        note = f"emergency cost £{round(extra,2)}" if extra > 0 else "recovery"
        projections.append(_month_obj(m, income, expenses, savings, note=note))

        if month_broke is None and savings <= 0:
            month_broke = m
            months_until_broke = m - 1

    composite = _composite_resilience(
        projections=projections,
        months_until_broke=months_until_broke,
        horizon_months=horizon_months,
        base_income=float(profile.monthly_income or 0.0),
        base_expenses=float(profile.total_expenses() or 0.0),
    )
    score = float(composite["composite_score"])

    summary = (
        f"Emergency simulation over {horizon_months} months. "
        f"Emergency amount £{round(amount,2)} spread over {spread_months} month(s)."
    )

    return {
        "scenario_type": "emergency",
        "monthly_projections": projections,
        "months_until_broke": months_until_broke,
        "month_broke": month_broke,
        "resilience_score": score,
        "score_breakdown": composite["breakdown"],
        "score_meta": composite["meta"],
        "summary": summary,
    }


def run_scenario(profile: ProfileSnapshot, *, scenario_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = params or {}
    scenario = (scenario_type or "").lower().strip()

    if scenario == "job_loss":
        return run_job_loss(
            profile,
            horizon_months=_get_horizon_months(params, default=12),
            income_replacement=float(params.get("income_replacement", 0.0)),
            cutback_percent=params.get("cutback_percent"),
            cutback_start_month=int(params.get("cutback_start_month", 2)),
        )

    if scenario == "promotion":
        return run_promotion(
            profile,
            horizon_months=_get_horizon_months(params, default=12),
            income_increase_percent=float(params.get("income_increase_percent", 20)),
            lifestyle_inflation_percent=float(params.get("lifestyle_inflation_percent", 0)),
        )

    if scenario == "emergency":
        return run_emergency(
            profile,
            horizon_months=_get_horizon_months(params, default=12),
            amount=float(params.get("amount", 1000)),
            spread_months=int(params.get("spread_months", 1)),
        )

    raise ValueError(f"Unknown scenario_type: {scenario_type}")
