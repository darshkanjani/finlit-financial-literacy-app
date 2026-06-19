"""

One router to rule them all.
main.py should include this router once under /api/v1.

Add new endpoints here, not in main.py.

TODO:
- as features become real, their routers will stop raising NotImplementedError.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    profile,
    spending,
    goals,
    dashboard,
    csv,
    stress_test,
    advice,
    chat,
    admin,
    legal,
    fx,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(spending.router, prefix="/spending", tags=["spending"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(csv.router, prefix="/csv", tags=["csv"])
api_router.include_router(stress_test.router, prefix="/stress-test", tags=["stress-test"])
api_router.include_router(advice.router, prefix="/advice", tags=["advice"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(legal.router, prefix="/legal", tags=["legal"])
api_router.include_router(fx.router, prefix="/fx", tags=["fx"])
