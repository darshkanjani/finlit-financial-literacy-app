"""

Goals endpoints.

Frontend usage:
- Goals page:
  - GET /goals
  - POST /goals
  - POST /parse
  - PUT /goals/{id}
  - DELETE /goals/{id}
- Forecast UI:
  - GET /goals/{id}/forecast
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.goals import GoalIn, GoalOut, GoalForecastOut
from app.services.goals_service import (
    list_goals,
    create_goal,
    update_goal,
    delete_goal,
    forecast_goal,
    goal_to_out,
)

from app.schemas.goals_ai import GoalParseIn, GoalParseOut
from app.services.goals_ai_service import parse_goal_text

router = APIRouter()


@router.get("", response_model=list[GoalOut])
def get_goals(db: Session = Depends(get_db), user=Depends(get_current_user)):
    goals = list_goals(db, user=user)
    return [goal_to_out(g) for g in goals]


@router.post("", response_model=GoalOut)
def add_goal(payload: GoalIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    goal = create_goal(db, user=user, payload=payload.model_dump())
    return goal_to_out(goal)


@router.put("/{goal_id}", response_model=GoalOut)
def edit_goal(goal_id: str, payload: GoalIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Using GoalIn for simplicity. If you want partial update later, make a GoalUpdate schema.
    goal = update_goal(db, user=user, goal_id=goal_id, payload=payload.model_dump())
    return goal_to_out(goal)


@router.delete("/{goal_id}")
def remove_goal(goal_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    delete_goal(db, user=user, goal_id=goal_id)
    return {"message": "Goal deleted"}


@router.get("/{goal_id}/forecast", response_model=GoalForecastOut)
def get_forecast(goal_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return forecast_goal(db, user=user, goal_id=goal_id)

@router.post("/parse", response_model=GoalParseOut)
def parse_goal(payload: GoalParseIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # This endpoint does NOT create a goal.
    # It returns a suggested structured goal for the user to review.
    return parse_goal_text(db, user=user, text=payload.text)
