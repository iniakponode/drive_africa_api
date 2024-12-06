
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import dotenv

# load the .env file
dotenv.load_dotenv()

# Database URL from settings
DATABASE_URL = os.getenv("DATABASE_URL")

# Create a new SQLAlchemy engine instance
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our classes definitions
Base = declarative_base()
