from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from pandaherd.core.config import settings

# Create engine
engine = create_engine(settings.database_url)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
