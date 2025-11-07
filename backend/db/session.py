from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

# --- SQLAlchemy Engine ---
engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)

# --- Session Factory ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_engine():
    """Return initialized SQLAlchemy engine."""
    return engine


def get_db():
    """Provide a database session to FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Run a test query to confirm DB connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL (Neon/Timescale) engine initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
