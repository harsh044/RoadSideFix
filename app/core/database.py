from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


# PostgreSQL database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,  # Change to True when debugging SQL
)


# Database session
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

class Base(DeclarativeBase):
    pass

# Single Base for all SQLAlchemy models
# Base = declarative_base()


# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()