# database/db.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from safedrive.database.base import SessionLocal

def get_db():
    """
    Dependency to get a SQLAlchemy session.
    This will ensure that the session is properly closed after use.
    
    Yields:
        db (SessionLocal): SQLAlchemy session object.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
