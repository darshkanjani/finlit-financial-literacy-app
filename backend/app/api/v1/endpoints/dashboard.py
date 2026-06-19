"""

Dashboard endpoint.

Frontend calls this once on dashboard load.
We return one JSON blob with everything needed to render.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import build_dashboard

router = APIRouter()


@router.get("", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return build_dashboard(db, user=user)
