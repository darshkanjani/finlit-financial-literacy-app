"""

Auth endpoints:
POST /register
POST /login
POST /logout
POST /passwordreset
GET  /me

Token is set as an HttpOnly cookie (not returned in JSON body).
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, ChangeRequest, UserOut, ForgotRequest, CheckForgotRequest, ResetRequest
from app.services.auth_service import register_user, login_user, change_password, forgot_password, check_forgot_token, reset_password

router = APIRouter()

# NOTE: set secure=True in production (HTTPS only)
_COOKIE_KWARGS = dict(
    key="access_token",
    httponly=True,
    samesite="lax",
    secure=False,  # switch to True in production
)


@router.post("/register", response_model=UserOut)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    token, user = register_user(db, email=payload.email, password=payload.password, name=payload.name)
    response.set_cookie(value=token, **_COOKIE_KWARGS)
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        literacy_score=user.literacy_score,
        is_admin=user.is_admin,
    )


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    token, user = login_user(db, email=payload.email, password=payload.password)
    response.set_cookie(value=token, **_COOKIE_KWARGS)
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        literacy_score=user.literacy_score,
        is_admin=user.is_admin,
    )


@router.post("/change-password", response_model=UserOut)
def changePassword(payload: ChangeRequest, response: Response, db: Session = Depends(get_db)):
    token, user = change_password(db, email=payload.email, password=payload.password, newpassword=payload.newpassword)
    response.set_cookie(value=token, **_COOKIE_KWARGS)
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        literacy_score=user.literacy_score,
        is_admin=user.is_admin,
    )

@router.post("/forgot-password")
async def forgotPassword(payload: ForgotRequest, response: Response, db: Session = Depends(get_db)):
    dev_token = await forgot_password(db, email=payload.email, link=payload.link)

    return {
        "detail": "If the account exists, an email has been sent with a password reset link",
        "dev_token": dev_token,  # None in production; useful for testing without email
    }

@router.post("/reset-password")
def resetPassword(payload: ResetRequest, response: Response, db: Session = Depends(get_db)):
    if check_forgot_token(db, token=payload.token):
        token, user = reset_password(db, email=payload.email, newpassword=payload.newpassword)
        response.set_cookie(value=token, **_COOKIE_KWARGS)
        return UserOut(
            id = user.id,
            email = user.email,
            name = user.name,
            literacy_score = user.literacy_score,
            is_admin = user.is_admin
        )

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        literacy_score=current_user.literacy_score,
        is_admin=current_user.is_admin,
    )
