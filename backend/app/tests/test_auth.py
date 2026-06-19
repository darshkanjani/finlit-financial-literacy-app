import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.deps import get_current_user
from app.core.jwt import decode_token
from app.services.auth_service import change_password, login_user, register_user


def _request_with_token(token: str | None) -> Request:
    headers = []
    if token:
        headers.append((b"cookie", f"access_token={token}".encode()))
    scope = {"type": "http", "headers": headers}
    return Request(scope)


def test_register_success(db_session):
    token, user = register_user(db_session, email="test@gmail.com", password="abc123", name="TestUser")

    assert isinstance(user.id, str)
    assert user.email == "test@gmail.com"
    assert user.name == "TestUser"
    assert user.is_admin is False
    assert isinstance(user.literacy_score, int)
    assert decode_token(token)["sub"] == user.id


def test_register_duplicate_email(db_session):
    register_user(db_session, email="test2@gmail.com", password="abc1234", name="TestUser2")

    with pytest.raises(HTTPException) as exc:
        register_user(db_session, email="test2@gmail.com", password="password3", name="TestUser5")

    assert exc.value.status_code == 400
    assert exc.value.detail == "Email already registered"


def test_login_success(db_session):
    _, created = register_user(db_session, email="test@gmail.com", password="abc123", name="TestUser")

    token, logged_in = login_user(db_session, email="test@gmail.com", password="abc123")

    assert logged_in.id == created.id
    assert logged_in.email == "test@gmail.com"
    assert decode_token(token)["sub"] == created.id


def test_login_wrong_password(db_session):
    register_user(db_session, email="test@gmail.com", password="abc123", name="TestUser")

    with pytest.raises(HTTPException) as exc:
        login_user(db_session, email="test@gmail.com", password="wrongpassword")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


def test_login_unknown_email(db_session):
    with pytest.raises(HTTPException) as exc:
        login_user(db_session, email="nobody@gmail.com", password="abc123")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


def test_get_current_user_authenticated(db_session):
    token, user = register_user(db_session, email="test@gmail.com", password="abc123", name="TestUser")

    current_user = get_current_user(_request_with_token(token), db_session)

    assert current_user.id == user.id
    assert current_user.email == "test@gmail.com"


def test_get_current_user_unauthenticated(db_session):
    with pytest.raises(HTTPException) as exc:
        get_current_user(_request_with_token(None), db_session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Missing token"


def test_change_password_success(db_session):
    register_user(db_session, email="test@gmail.com", password="abc123", name="TestUser")

    token, user = change_password(
        db_session,
        email="test@gmail.com",
        password="abc123",
        newpassword="newpass456",
    )

    assert user.email == "test@gmail.com"
    assert decode_token(token)["sub"] == user.id

    with pytest.raises(HTTPException):
        login_user(db_session, email="test@gmail.com", password="abc123")

    _, relogged = login_user(db_session, email="test@gmail.com", password="newpass456")
    assert relogged.id == user.id


def test_change_password_wrong_old(db_session):
    register_user(db_session, email="test@gmail.com", password="abc123", name="TestUser")

    with pytest.raises(HTTPException) as exc:
        change_password(
            db_session,
            email="test@gmail.com",
            password="wrongpass",
            newpassword="newpass456",
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"
