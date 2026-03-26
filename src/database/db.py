"""Database engine, session factory and dependency helpers."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.conf.config import get_settings

settings = get_settings()
engine = create_engine(settings.db_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""



def get_db():
    """Yield a database session and close it after request handling."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
