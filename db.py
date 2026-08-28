from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
import os

database_url = os.getenv("DATABASE_URL", "sqlite:///database.db")

engine = create_engine(database_url, echo=True)

Base = declarative_base()


session = sessionmaker(bind=engine)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()