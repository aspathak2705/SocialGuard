import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def create_configured_engine():
    target_url = settings.DATABASE_URL
    connect_args = {}
    engine_kwargs = {}

    if target_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    else:
        # Check if Postgres is reachable before binding pool
        try:
            temp_engine = create_engine(target_url, connect_args={"connect_timeout": 3})
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            # If successful, use Postgres
            engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
            engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
            logger.info("Connected to configured PostgreSQL database.")
            return temp_engine
        except Exception as e:
            if settings.DATABASE_REQUIRE_POSTGRES:
                logger.error(f"DATABASE_REQUIRE_POSTGRES is True and PostgreSQL is unreachable: {e}")
                raise RuntimeError(
                    f"Hosted deployment requires PostgreSQL connectivity, but connection failed: {e}"
                )
            logger.warning(
                f"Configured PostgreSQL unreachable ({e}). Using local durable SQLite fallback 'socialguard.db'."
            )
            target_url = "sqlite:///./socialguard.db"
            connect_args["check_same_thread"] = False

    return create_engine(target_url, connect_args=connect_args, **engine_kwargs)

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
