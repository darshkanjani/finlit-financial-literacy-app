"""

Admin shapes.
"""

from pydantic import BaseModel


class AdminUserOut(BaseModel):
    id: str
    email: str
    created_at: str
    has_profile: bool
    is_admin: bool = False


class AdminStatsOut(BaseModel):
    total_users: int
    profiles_completed: int
    stress_tests_run: int
    advice_generated: int
