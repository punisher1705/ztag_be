from __future__ import annotations
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

class Base(DeclarativeBase):
    """Declarative base shared by every ORM model in the app."""

def build_engine(database_url: str, *, echo: bool = False):
    print("Inside build engine")
    return create_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
        pool_recycle=1800
    )

def build_session_factoru(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class SessionManager:
    def __init__(self, database_url: str, *, echo: bool = False) -> None:
        self.engine = build_engine(database_url, echo=echo)
        self._session_factory = build_session_factoru(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()