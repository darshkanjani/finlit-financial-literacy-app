"""

FinLit database schema (SQLAlchemy ORM).

This file is the schema. Tables are defined as Python classes.

How tables get created in dev:
- app/main.py imports this module
- app/main.py calls Base.metadata.create_all(engine)
- create_all() only creates missing tables (it does NOT wipe data)

Practical workflow for coursework:
- If you change schema during dev, easiest is to delete finlit.db and restart
  (we’re not doing migrations unless forced)

We store:
- User + login info
- One profile per user (the onboarding form)
- Goals, stress tests, advice history
- Optional: csv_uploads (aggregated totals only, no raw transactions)
"""

import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)

    # Keep email plaintext so login can query by email easily.
    # If we later encrypt it, we'd need a different lookup strategy.
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # Stores Argon2/bcrypt hash of either:
    # - plaintext password, OR
    # - client-side SHA256(password) if we choose that route
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    name: Mapped[str | None] = mapped_column(String, nullable=True)

    # 1..5 controls how simple/technical explanations are in advice/chat.
    literacy_score: Mapped[int] = mapped_column(Integer, default=3)

    # Used by admin endpoints.
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Cascades mean: deleting a user deletes all related rows.
    profile = relationship("FinancialProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    stress_tests = relationship("StressTestResult", back_populates="user", cascade="all, delete-orphan")
    advice_history = relationship("AdviceHistory", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    csv_uploads = relationship("CsvUpload", back_populates="user", cascade="all, delete-orphan")
    forgot_password_tokens = relationship("ForgotPassword", back_populates="user", cascade = "all, delete-orphan")

class ForgotPassword(Base):
    """

    One row per user (1:1). Should limit each user to one forgot password request per hour. 
    """
    __tablename__ = "forgot_password_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    token_hash: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    used: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="forgot_password_tokens")


class FinancialProfile(Base):
    """

    One row per user (1:1). This is basically the onboarding form saved in DB.
    Flat columns keep it simple for breakdown calculations and stress tests.
    """
    __tablename__ = "financial_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    monthly_income: Mapped[float] = mapped_column(Float, nullable=False)
    
    # NEW: lightweight “context” fields (optional, broad bands)
    age_band: Mapped[str | None] = mapped_column(String, nullable=True)  # "18-24", "25-34", etc.
    employment_status: Mapped[str | None] = mapped_column(String, nullable=True)  # student/employed/self_employed/unemployed
    occupation_category: Mapped[str | None] = mapped_column(String, nullable=True)  # tech/finance/retail/healthcare/other
    dependents_count: Mapped[int] = mapped_column(Integer, default=0)

    # NEW: buffer makes stress tests meaningful
    savings_buffer: Mapped[float] = mapped_column(Float, default=0)

    rent: Mapped[float] = mapped_column(Float, default=0)
    bills: Mapped[float] = mapped_column(Float, default=0)
    subscriptions: Mapped[float] = mapped_column(Float, default=0)
    loan_repayments: Mapped[float] = mapped_column(Float, default=0)

    groceries: Mapped[float] = mapped_column(Float, default=0)
    transport: Mapped[float] = mapped_column(Float, default=0)
    entertainment: Mapped[float] = mapped_column(Float, default=0)
    eating_out: Mapped[float] = mapped_column(Float, default=0)
    clothing: Mapped[float] = mapped_column(Float, default=0)
    health: Mapped[float] = mapped_column(Float, default=0)
    other: Mapped[float] = mapped_column(Float, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class UserPreference(Base):
    """
    Per-user UI preferences.
    Keep separate from financial profile to avoid schema churn in core calculations.
    """
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    currency_code: Mapped[str] = mapped_column(String, default="GBP", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)

    goal_name: Mapped[str] = mapped_column(String, nullable=False)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_amount: Mapped[float] = mapped_column(Float, default=0)

    target_date: Mapped[date | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")


class StressTestResult(Base):
    __tablename__ = "stress_test_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)

    scenario_type: Mapped[str] = mapped_column(String, nullable=False)
    params: Mapped[dict] = mapped_column(JSON, default=dict)

    # List of month objects; JSON keeps it simple.
    monthly_projections: Mapped[list] = mapped_column(JSON, default=list)

    months_until_broke: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resilience_score: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="stress_tests")


class AdviceHistory(Base):
    __tablename__ = "advice_history"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)

    advice_text: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[list] = mapped_column(JSON, default=list)
    sources: Mapped[list] = mapped_column(JSON, default=list)

    literacy_level_used: Mapped[int] = mapped_column(Integer, default=3)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="advice_history")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)

    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")


class CsvUpload(Base):
    """

    Optional table.
    We store only aggregated, already-processed totals and warnings.
    No transaction-level rows.
    """
    __tablename__ = "csv_uploads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)

    filename: Mapped[str | None] = mapped_column(String, nullable=True)
    category_totals: Mapped[dict] = mapped_column(JSON, default=dict)
    warnings: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="csv_uploads")
