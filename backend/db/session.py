# backend/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

try:
    # Create SQLAlchemy engine
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,  # Set True for SQL debugging
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    logger.info("✅ PostgreSQL (Neon/Timescale) engine initialized successfully.")

except Exception as e:
    logger.error(f"❌ Failed to initialize database engine: {e}")
    engine = None


# Scoped session factory
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


def get_db():
    """
    Dependency for FastAPI endpoints.
    Provides a transactional session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
    finally:
        db.close()
