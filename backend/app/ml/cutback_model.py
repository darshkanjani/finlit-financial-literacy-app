"""

Tiny ML model for "cutback_percent" prediction.

Goal:
- given a user's profile ratios + basic context
- predict a reasonable default cutback_percent for job loss scenario
- used ONLY when frontend doesn't provide cutback_percent

Why this is good for uni:
- you can say "ML used to personalise stress test assumptions"
- still explainable + deterministic simulation
- training is on synthetic data (no privacy issues, no external datasets needed)

Implementation:
- build synthetic dataset
- train a small RandomForestRegressor
- persist it to disk (train once, reuse many times)
- if model isn't available, fall back to rule-based defaults (engine does that)

How it integrates:
- stress_service.py (job_loss) calls:
    model = load_model(MODEL_PATH_DEFAULT)
    pred = predict_cutback_percent(model, features)
    params["cutback_percent"] = pred
- stress_engine.py then uses params["cutback_percent"] deterministically in simulation.
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import joblib  # type: ignore
except Exception:
    joblib = None

try:
    from sklearn.ensemble import RandomForestRegressor  # type: ignore
except Exception:
    RandomForestRegressor = None


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
# IMPORTANT:
# Use a path relative to this file so it works regardless of cwd.
MODEL_PATH_DEFAULT = str(Path(__file__).resolve().parent / "artifacts" / "cutback_model.joblib")


# -------------------------------------------------------------------
# Feature schema
# -------------------------------------------------------------------

@dataclass
class CutbackFeatures:
    needs_ratio: float
    wants_ratio: float
    debt_ratio: float
    income: float
    dependents_count: int
    employment_status: str | None
    literacy_score: int


# -------------------------------------------------------------------
# Small helpers
# -------------------------------------------------------------------

def _employment_to_num(status: str | None) -> int:
    s = (status or "").lower().strip()
    if s == "employed":
        return 3
    if s == "self_employed":
        return 2
    if s == "student":
        return 1
    if s == "unemployed":
        return 0
    return 1  # unknown -> treat as "student-ish"


def _clamp(x: float, lo: float, hi: float) -> float:
    try:
        x = float(x)
    except Exception:
        return lo
    return max(lo, min(hi, x))


def features_to_vector(f: CutbackFeatures) -> list[float]:
    """
    Keep feature ordering consistent forever.
    If you change this, you must retrain the model.
    """
    return [
        _clamp(f.needs_ratio, 0.0, 2.0),
        _clamp(f.wants_ratio, 0.0, 2.0),
        _clamp(f.debt_ratio, 0.0, 2.0),
        _clamp(f.income, 0.0, 1_000_000.0),
        float(max(0, min(20, int(f.dependents_count)))),
        float(_employment_to_num(f.employment_status)),
        float(max(1, min(5, int(f.literacy_score)))),
    ]


# -------------------------------------------------------------------
# Synthetic label (ground truth) rule
# -------------------------------------------------------------------

def _label_cutback_rule(f: CutbackFeatures) -> float:
    """
    Synthetic "ground truth" for training.
    Encodes our intuition + adds noise:

    - high wants_ratio => more cut possible
    - high needs_ratio => less flexibility
    - dependents => less flexibility
    - student/unemployed => slightly less flexibility (already lean)
    - literacy => tiny positive effect (planning)

    Output is clamped to 5%..80%.
    """
    base = 0.35

    base += 0.35 * _clamp(f.wants_ratio, 0.0, 1.0)  # more wants => more cut possible
    base -= 0.25 * _clamp(f.needs_ratio, 0.0, 1.0)  # more needs => less flex
    base -= 0.10 * _clamp(f.debt_ratio, 0.0, 1.0)   # debt reduces flexibility a bit

    if (f.dependents_count or 0) > 0:
        base -= 0.12

    emp = _employment_to_num(f.employment_status)
    if emp <= 1:  # student/unemployed
        base -= 0.08

    base += 0.02 * (max(1, min(5, int(f.literacy_score))) - 3)

    # small noise
    base += random.uniform(-0.05, 0.05)

    return _clamp(base, 0.05, 0.80)


# -------------------------------------------------------------------
# Dataset generation
# -------------------------------------------------------------------

def generate_synthetic_dataset(n: int = 4000) -> tuple[list[list[float]], list[float]]:
    """
    Generates synthetic training data:
    X: feature vectors
    y: cutback_percent labels
    """
    X: list[list[float]] = []
    y: list[float] = []

    statuses = [None, "student", "employed", "self_employed", "unemployed"]

    for _ in range(n):
        income = random.uniform(800, 6000)

        # sample ratios somewhat realistically
        needs_ratio = _clamp(random.gauss(0.55, 0.12), 0.15, 0.95)
        wants_ratio = _clamp(random.gauss(0.25, 0.12), 0.00, 0.75)
        debt_ratio = _clamp(random.gauss(0.10, 0.10), 0.00, 0.60)

        dependents = random.choice([0, 0, 0, 1, 2])  # skew to 0 for demo users
        status = random.choice(statuses)
        literacy = random.choice([1, 2, 3, 4, 5])

        f = CutbackFeatures(
            needs_ratio=needs_ratio,
            wants_ratio=wants_ratio,
            debt_ratio=debt_ratio,
            income=income,
            dependents_count=dependents,
            employment_status=status,
            literacy_score=literacy,
        )

        X.append(features_to_vector(f))
        y.append(_label_cutback_rule(f))

    return X, y


# -------------------------------------------------------------------
# Train / Save / Load
# -------------------------------------------------------------------

def train_and_save_model(model_path: str = MODEL_PATH_DEFAULT, n: int = 4000) -> dict[str, Any]:
    """
    Train the model once and persist to disk.

    Typical workflow:
      python -m app.ml.cutback_model
    or
      python scripts/train_cutback_model.py
    """
    if RandomForestRegressor is None or joblib is None:
        return {"ok": False, "reason": "scikit-learn and/or joblib not installed"}

    X, y = generate_synthetic_dataset(n=n)

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        max_depth=10,
        n_jobs=-1,
    )
    model.fit(X, y)

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)

    return {"ok": True, "model_path": model_path, "trained_rows": n}


def load_model(model_path: str = MODEL_PATH_DEFAULT):
    """
    Loads trained model if present. Returns None if missing/unreadable.
    """
    if joblib is None:
        return None
    if not os.path.exists(model_path):
        return None
    try:
        return joblib.load(model_path)
    except Exception:
        return None


# -------------------------------------------------------------------
# Predict
# -------------------------------------------------------------------

def predict_cutback_percent(model, features: CutbackFeatures) -> float | None:
    """
    Predict cutback_percent (0.05..0.80). Returns None on any failure.
    """
    if model is None:
        return None
    try:
        vec = [features_to_vector(features)]
        pred = float(model.predict(vec)[0])
        return _clamp(pred, 0.05, 0.80)
    except Exception:
        return None


# -------------------------------------------------------------------
# Convenience: train from command line
# -------------------------------------------------------------------

if __name__ == "__main__":
    out = train_and_save_model(MODEL_PATH_DEFAULT, n=4000)
    print(out)
    if out.get("ok"):
        print("Model trained & saved. Stress tests will use ML when cutback_percent is omitted (job_loss only).")