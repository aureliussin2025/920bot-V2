from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
import os

# Use DATABASE_URL when Docker supplies it; otherwise use a local SQLite file.
database_url = os.getenv("DATABASE_URL", "sqlite:///database.db")

# An engine holds the database connection settings. It is not a session or row.
engine = create_engine(database_url, echo=True)

# All SQLAlchemy table models inherit from this shared Base.
Base = declarative_base()


# A factory: calling session() creates a fresh unit of database work.
session = sessionmaker(bind=engine)

def get_db():
    # FastAPI runs this dependency for each request that needs a database.
    db = session()
    try:
        # yield hands the session to the endpoint; execution resumes afterward.
        yield db
    finally:
        # Always release it, even if the endpoint raises an HTTP error.
        db.close()
