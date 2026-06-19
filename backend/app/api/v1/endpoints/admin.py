"""

Admin endpoints.
All routes require an authenticated admin user.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.schemas.admin import AdminUserOut, AdminStatsOut
from app.schemas.common import MessageOut
from app.services.admin_service import list_users, get_stats, delete_user

router = APIRouter()


@router.get("/users", response_model=list[AdminUserOut])
def users(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return list_users(db)


@router.get("/stats", response_model=AdminStatsOut)
def stats(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return get_stats(db)


@router.delete("/users/{user_id}", response_model=MessageOut)
def remove_user(user_id: str, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    delete_user(db, user_id=user_id)
    return {"message": "User deleted"}
