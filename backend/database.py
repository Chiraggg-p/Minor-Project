# backend/database.py
# PostgreSQL + PostGIS connection handler

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# IMPORTANT: Reserved characters in password are already encoded correctly (%40 = @)
DATABASE_URL = "postgresql://postgres:db%401010@localhost:5432/traffix_db"

# Create engine with safety features
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,         # Avoid stale connection errors
    echo=False                  # Turn to True only for debugging
)

# Create DB session class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for SQLAlchemy models
Base = declarative_base()
