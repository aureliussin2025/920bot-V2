from sqlalchemy import create_engine, DateTime, text, MetaData, Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from db import Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    buy_price = Column(Float, nullable=False)
    buy_time = Column(DateTime, nullable = False)
    sell_price = Column(Float)
    sell_time = Column(DateTime)
    pnl = Column(Float)

class ReturnTrade(BaseModel):
    id: int
    ticker: str
    buy_price: float
    buy_time: datetime
    sell_price: Optional[float]
    sell_time: Optional[datetime]
    pnl: Optional[float]

class ReturnEarning(BaseModel):
    earnings: float


