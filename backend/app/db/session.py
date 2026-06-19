"""

Database engine + session factory.

Mental model:
- engine = points at the DB (SQLite file by default)
- SessionLocal() = short-lived DB session used per request

SQLite note:
- check_same_thread=False avoids thread issues in FastAPI dev mode.

TODO:
- if we move off SQLite later, update engine settings and remove SQLite-specific args.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
