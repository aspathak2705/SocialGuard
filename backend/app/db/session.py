import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings, _ROOT_DIR

from urllib.parse import urlparse

logger = logging.getLogger(__name__)

Base = declarative_base()


def log_database_diagnostics(url: str, backend: str):
    """Logs safe database configuration diagnostics without exposing passwords."""
    parsed = urlparse(url)
    has_password = bool(parsed.password)
    safe_host = parsed.hostname or "local_file"
    safe_port = parsed.port or ("5432" if backend == "postgresql" else "N/A")
    logger.info(
        f"[DB_CONFIG] Backend: '{backend}' | Host: '{safe_host}' | Port: {safe_port} | "
        f"Password Configured: {has_password} | SSL Mode: '{settings.DATABASE_SSL_MODE}'"
    )


def create_configured_engine():
    backend = settings.DATABASE_BACKEND
    target_url = settings.get_effective_database_url()

    log_database_diagnostics(target_url, backend)

    connect_args = {}
    engine_kwargs = {}

    if backend == "sqlite" or target_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        return create_engine(target_url, connect_args=connect_args, **engine_kwargs)

    # PostgreSQL / Supabase
    connect_args["connect_timeout"] = 5
    engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

    try:
        temp_engine = create_engine(target_url, connect_args=connect_args, **engine_kwargs)
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully established connection to PostgreSQL database.")
        return temp_engine
    except Exception as e:
        safe_msg = str(e).split("@")[-1] if "@" in str(e) else str(e)
        logger.error(f"Failed connecting to configured PostgreSQL database: {safe_msg}")
        if settings.DATABASE_REQUIRE_POSTGRES:
            raise RuntimeError(f"Required PostgreSQL database is unreachable: {safe_msg}")

        # If in development and not strictly required, provide controlled fallback with explicit log
        logger.warning(
            "DATABASE_REQUIRE_POSTGRES is False. Falling back to local SQLite 'socialguard.db' for development session."
        )
        fallback_url = f"sqlite:///{(_ROOT_DIR / settings.DATABASE_SQLITE_PATH).resolve()}"
        return create_engine(fallback_url, connect_args={"check_same_thread": False})


engine = create_configured_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



from contextlib import contextmanager


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for standalone database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connectivity() -> bool:
    """Verifies active connectivity to configured database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connectivity check failed: {e}")
        return False


def init_db():
    """Initializes schema tables if not existing."""
    Base.metadata.create_all(bind=engine)
