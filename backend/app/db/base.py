"""

SQLAlchemy base class.
All ORM models inherit from Base.

TODO:
- keep stable
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
