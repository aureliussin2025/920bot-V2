from sqlalchemy import create_engine, DateTime, text, MetaData, Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from db import Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# SQLAlchemy model: each Trade object maps to one row in the "trades" table.
# A BUY fills the required buy fields; a SELL later fills the nullable fields.
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    avg_buy_price = Column(Float, nullable=False)
    open_time = Column(DateTime, nullable=False)
    # NULL in these columns means the position has not been closed yet.
    sell_price = Column(Float)
    sell_time = Column(DateTime)
    pnl = Column(Float)
    strategy = Column(String, nullable =False)
    quantity = Column(Integer, nullable=False, default=0)
    total_value = Column(Float, nullable=False, default=0)

#buy table - to fill out details about buy, including the time and price of each buy
class Buy(Base):
    __tablename__ = "buys"

    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    buy_price = Column(Float,  nullable=False)
    buy_time = Column(DateTime, nullable=False)

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    ticker = Column(String,nullable=False)
    action = Column(String,nullable=False)
    price = Column(Float,  nullable=False)
    time = Column(DateTime, nullable=False)
    strategy = Column(String,nullable=False)

# Pydantic response model: describes what the API returns, not a database table.
# Unlike Trade above, this class does not create or modify database columns.
class ReturnTrade(BaseModel):
    id: int
    ticker: str
    avg_buy_price: float
    open_time: datetime
    # Optional permits None for an open trade in the JSON response.
    sell_price: Optional[float]
    sell_time: Optional[datetime]
    pnl: Optional[float]
    total_value: float
    strategy: str
    quantity: int

#Idempotency response model
class ReturnDuplicateResponse(BaseModel):
    status: str


# The /earnings endpoint returns an object such as {"earnings": 1.25}.
class ReturnEarning(BaseModel):
    earnings: float

