from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

# The shape of the incoming TradingView JSON. Pydantic/FastAPI validate it
# before create_trade() runs; invalid bodies receive a validation response.
class TradeSignal(BaseModel):
    idempotency_key: int
    # Identifying key
    ticker: str
    # Literal allows only these two exact strings, not arbitrary actions.
    action: Literal['buy', 'sell']
    # Reject zero or negative prices.
    price: float = Field(gt=0)
    # A timestamp string in JSON is parsed into a Python datetime.
    time: datetime
    # Strategy name
    strategy: str
