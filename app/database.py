from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker, Session

_engine = None
SessionLocal: scoped_session[Session] | None = None

class Base(DeclarativeBase):
    pass

def init_engine_and_session(database_url: str) -> None:
    global _engine, SessionLocal
    _engine = create_engine(database_url, echo=False, future=True)
    SessionLocal = scoped_session(sessionmaker(bind=_engine, autoflush=False, autocommit=False))

def get_session() -> Session:
    assert SessionLocal is not None, "SessionLocal not initialized. Call init_engine_and_session first."
    return SessionLocal()

def init_db_and_seed() -> None:
    """
    Creates tables and seeds a default admin user (if not present).
    """
    from .models import User  # import after Base defined
    Base.metadata.create_all(bind=_engine)

    from passlib.hash import bcrypt
    with get_session() as s:
        if not s.query(User).filter_by(email="admin@example.com").first():
            u = User(email="admin@example.com", password_hash=bcrypt.hash("admin123"), role="admin")
            s.add(u)
            s.commit()