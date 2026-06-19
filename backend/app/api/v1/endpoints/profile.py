"""

Profile endpoints.

Frontend flow:
- Onboarding form submits -> POST /profile
- When user reopens onboarding/settings -> GET /profile

Notes:
- Keep endpoints thin: validate -> call service -> return response.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.profile import ProfileIn, ProfileOut
from app.services.profile_service import upsert_profile, get_profile, profile_to_out

router = APIRouter()


@router.post("", response_model=ProfileOut)
def create_or_update_profile(
    payload: ProfileIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # This is intentionally "upsert" so the form can be resubmitted.
    profile = upsert_profile(db, user=user, payload_dict=payload.model_dump())
    return profile_to_out(db=db, profile=profile, user=user)


@router.get("", response_model=ProfileOut)
def read_profile(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    profile = get_profile(db, user=user)
    return profile_to_out(db=db, profile=profile, user=user)
