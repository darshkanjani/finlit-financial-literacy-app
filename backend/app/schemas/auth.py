"""

Auth request/response models.

Note: AuthResponse with a token field is no longer used - the JWT is now
delivered via an HttpOnly cookie, not the response body. Endpoints return
UserOut directly.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangeRequest(BaseModel):
    email: EmailStr
    password: str
    newpassword: str = Field(min_length=6)

class ForgotRequest(BaseModel):
    email: EmailStr
    link: str

class CheckForgotRequest(BaseModel):
    reset_link: str

class ResetRequest(BaseModel):
    email: EmailStr
    newpassword: str = Field(min_length=6)
    token: str

class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str | None = None
    literacy_score: int
    is_admin: bool
