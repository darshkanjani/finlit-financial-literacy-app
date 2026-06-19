"""

Advice endpoints.
- POST /advice           -> one-shot advice (stores AdviceHistory)
- GET  /advice/history   -> list saved advice
- POST /advice/goal-plan -> goal coaching plan suggestions (no DB write; uses plan_service)

Outputs come from schemas/advice.py (AdviceOut, AdviceHistoryOut).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.advice import AdviceIn, AdviceOut, AdviceHistoryOut
from app.schemas.plan import GoalPlanIn, GoalPlanOut

from app.services.plan_service import build_goal_plan
from app.services.advice_service import clear_advice_history, generate_advice, list_advice_history

router = APIRouter()


@router.post("", response_model=AdviceOut)
def advice(payload: AdviceIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return generate_advice(db, user=user, message=payload.message)


@router.get("/history", response_model=list[AdviceHistoryOut])
def history(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_advice_history(db, user=user)


@router.delete("/history")
def clear_history(db: Session = Depends(get_db), user=Depends(get_current_user)):
    deleted = clear_advice_history(db, user=user)
    return {"deleted": deleted}


@router.post("/goal-plan", response_model=GoalPlanOut)
def goal_plan(payload: GoalPlanIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return build_goal_plan(db, user=user, goal_id=payload.goal_id)
