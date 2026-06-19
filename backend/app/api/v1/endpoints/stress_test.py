"""

Stress test endpoints.
- POST /stress-test/run        -> run a scenario and store StressTestResult
- GET  /stress-test/history    -> list recent runs
- GET  /stress-test/resilience -> quick summary for dashboard

TODO (Darsh):
- If you want "choose scenarios", frontend can send scenario_type + params.
- Keep this deterministic + explainable (uni project, not overkill ML).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user

try:
    from app.schemas.stress_test import StressTestIn, StressTestOut, StressTestSummaryOut
except Exception:  # pragma: no cover
    from pydantic import BaseModel

    class StressTestIn(BaseModel):
        scenario_type: str
        params: dict = {}

    class StressTestOut(BaseModel):
        id: str
        scenario_type: str
        params: dict
        monthly_projections: list
        months_until_broke: int | None = None
        resilience_score: float = 0.0

    class StressTestSummaryOut(BaseModel):
        overall_score: float
        rating: str
        weakest_scenario: str | None = None

from app.services.stress_service import run_stress_test, list_stress_history, resilience_summary

router = APIRouter()


@router.post("/run", response_model=StressTestOut)
def run(
    payload: StressTestIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return run_stress_test(db, user=user, scenario_type=payload.scenario_type, params=payload.params)


@router.get("/history", response_model=list[StressTestOut])
def history(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return list_stress_history(db, user=user, limit=15)


@router.get("/resilience", response_model=StressTestSummaryOut)
def resilience(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return resilience_summary(db, user=user)
