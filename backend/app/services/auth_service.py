"""
Authentication service logic.

The service handles registration, login, password changes and password reset tokens.
Email credentials are loaded from environment variables. No SMTP credentials should
be hardcoded in source code.
"""

from datetime import datetime, timedelta
import logging

from fastapi import HTTPException, status
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jwt import create_access_token, decode_token
from app.core.security import hash_secret, verify_secret
from app.db.models import ForgotPassword, User

logger = logging.getLogger(__name__)


def register_user(db: Session, *, email: str, password: str, name: str | None):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=email,
        password_hash=hash_secret(password),
        name=name,
        literacy_score=3,
        is_admin=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id)
    return token, user


def login_user(db: Session, *, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_secret(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user_id=user.id)
    return token, user


def change_password(db: Session, *, email: str, password: str, newpassword: str):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_secret(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.password_hash = hash_secret(newpassword)

    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id)
    return token, user


def _mail_configured() -> bool:
    return bool(settings.MAIL_USERNAME and settings.MAIL_PASSWORD and settings.MAIL_FROM)


async def _send_reset_email(reset_link: str, *, email: str) -> bool:
    """
    Send a password reset email if SMTP settings are configured.

    In the public portfolio version, SMTP credentials are intentionally not included.
    If mail settings are missing, the function logs and returns False instead of
    failing the whole request.
    """
    if not _mail_configured():
        logger.warning("Password reset email not sent because SMTP settings are not configured.")
        return False

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
    )

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"Click the link to reset your password:\n{reset_link}",
        subtype="plain",
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return True


async def forgot_password(db: Session, *, email: str, link: str):
    """
    Generate a one-time reset token and send a reset link if the account exists.

    The API intentionally does not reveal whether an email address exists.
    Returning the raw token is disabled by default and is only intended for local
    development when RETURN_RESET_TOKEN_IN_RESPONSE=true.
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    token = create_access_token(user_id=user.id)
    token_hash = hash_secret(token)
    expires = datetime.utcnow() + timedelta(hours=1)

    forgot_entry = db.query(ForgotPassword).filter(ForgotPassword.user_id == user.id).first()
    if forgot_entry:
        forgot_entry.token_hash = token_hash
        forgot_entry.expires_at = expires
        forgot_entry.used = False
        forgot_entry.created_at = datetime.utcnow()
    else:
        forgot_entry = ForgotPassword(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires,
        )
        db.add(forgot_entry)

    db.commit()
    db.refresh(forgot_entry)

    reset_link = f"{link}/reset-password?token={token}"
    await _send_reset_email(reset_link, email=email)

    if settings.RETURN_RESET_TOKEN_IN_RESPONSE:
        return token
    return None


def clean_forgot_password_table(*, db: Session):
    db.query(ForgotPassword).filter(ForgotPassword.expires_at < datetime.utcnow()).delete()
    db.commit()

    db.query(ForgotPassword).filter(ForgotPassword.used == True).delete()  # noqa: E712
    db.commit()


def check_forgot_token(db: Session, *, token: str):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired reset token")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token")

    clean_forgot_password_table(db=db)

    forgot_entry = db.query(ForgotPassword).filter(ForgotPassword.user_id == user_id).first()

    if not forgot_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reset token not found")

    if forgot_entry.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token already used")

    if not verify_secret(token, forgot_entry.token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token")

    forgot_entry.used = True
    db.commit()
    db.refresh(forgot_entry)

    return True


def reset_password(db: Session, *, email: str, newpassword: str):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.password_hash = hash_secret(newpassword)

    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id)
    return token, user
