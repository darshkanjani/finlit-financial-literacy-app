"""

Spending endpoints.

Frontend usage:
- Dashboard can call this OR dashboard endpoint can embed it later.
- Spending page calls GET /spending/breakdown and draws charts.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.spending import SpendingBreakdownOut
from app.services.spending_service import compute_breakdown

router = APIRouter()


@router.get("/breakdown", response_model=SpendingBreakdownOut)
def breakdown(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return compute_breakdown(db, user=user)
