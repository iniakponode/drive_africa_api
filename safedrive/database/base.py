
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import dotenv

# Load the .env file
dotenv.load_dotenv()

# Database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# SQLAlchemy engine and session
engine = create_engine(DATABASE_URL, 
                       pool_pre_ping=True,   # ✅ Checks connection before using
                       pool_recycle=3600,
                       echo=True),
                       
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for ORM models
Base = declarative_base()

