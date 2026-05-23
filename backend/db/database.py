from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from db.models import Base

DATABASE_URL = "sqlite:///./study_assistant.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def create_tables() -> None:
    """Call once on startup — creates all tables if not exist."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Returns a raw session. Caller must close it."""
    return SessionLocal()
