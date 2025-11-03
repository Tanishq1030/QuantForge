from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Read database URL from environment variable or fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://neondb_owner:npg_Z0tKsEky2dpw@ep-polished-smoke-a187h654-pooler.ap-southeast-1.aws.neon.tech/quantforge_db?sslmode=require&channel_binding=require"
)

def get_engine():
    """Return a SQLAlchemy engine connected to the configured PostgreSQL database."""
    engine = create_engine(DATABASE_URL, echo=False, future=True)
    return engine


# Optional: session factory for app-wide use
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
