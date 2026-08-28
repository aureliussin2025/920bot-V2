from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class TradeSignal(BaseModel):
    ticker: str
    action: Literal['buy', 'sell']
    price: float = Field(gt=0)
    time: datetime
