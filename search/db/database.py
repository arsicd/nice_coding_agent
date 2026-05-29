from pathlib import Path

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from core.config import settings

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.postgres_uri, pool_size=5, max_overflow=10, pool_pre_ping=True
        )

        @event.listens_for(_engine, "connect", insert=True)
        def set_search_path(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute(f'SET search_path TO "{settings.db_schema}", public')
            cursor.close()
            dbapi_connection.commit() if not dbapi_connection.autocommit else None

    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal


def new_session():
    return get_session_local()()


def get_db():
    db = new_session()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_migrated():
    project_root = Path(__file__).resolve().parent.parent.parent
    cfg = Config(str(project_root / "infra" / "alembic.ini"))
    command.upgrade(cfg, "head")
