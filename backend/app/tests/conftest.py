import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import User


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def make_user(db_session):
    def _make_user(**overrides):
        user = User(
            email=overrides.pop("email", f"{uuid.uuid4().hex}@test.local"),
            password_hash=overrides.pop("password_hash", "not-used-in-this-test"),
            name=overrides.pop("name", "Test User"),
            literacy_score=overrides.pop("literacy_score", 3),
            is_admin=overrides.pop("is_admin", False),
            **overrides,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make_user
