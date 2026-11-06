from fastapi import FastAPI, Depends,HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from schemas import TradeSignal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update
from db import Base, engine, get_db
from models import Trade, ReturnTrade, ReturnEarning, Buy, Signal, ReturnDuplicateResponse


# Create tables described by the SQLAlchemy models if they do not exist yet.
# This does not update the structure of a table that already exists.
Base.metadata.create_all(bind=engine)

app = FastAPI()

DASHBOARD_PATH = Path(__file__).with_name("dashboard.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    """Serve the small read-only trade dashboard."""
    return FileResponse(DASHBOARD_PATH)

# TradingView sends a JSON signal here. FastAPI turns that JSON into a
# TradeSignal, while Depends(get_db) provides one database session per request.
# response_model controls the shape of a successful response sent back as JSON.
@app.post("/920bot/webhook", status_code=201, response_model=ReturnTrade|ReturnDuplicateResponse)
def create_trade(tradeSignal: TradeSignal, db: Session = Depends(get_db)):

    #invalid action check
    if tradeSignal.action not in ("buy", "sell"):
        raise HTTPException(
            status_code=422,
            detail="Invalid action"
        )

    #first log the action to check for idemptoncy
    duplicate_trade_signal_check = db.query(Signal).filter(
        Signal.id == tradeSignal.idempotency_key
    ).first()
    
    if duplicate_trade_signal_check is not None:
        return ReturnDuplicateResponse(
            status = "duplicate signal"
        )
    try:
        signal = Signal(
            id = tradeSignal.idempotency_key,
            ticker = tradeSignal.ticker,
            action = tradeSignal.action,
            price = tradeSignal.price,
            time = tradeSignal.time,
            strategy = tradeSignal.strategy
        )
        db.add(signal)
        db.flush()
    
    #idempotency
    except IntegrityError:
        db.rollback()
    
        existing_signal = db.get(
            Signal,
            tradeSignal.idempotency_key
        )
    
        if existing_signal is not None:
            return ReturnDuplicateResponse(
                status = "duplicate signal"
            )
                    
        raise

    if tradeSignal.action == 'buy':
        try:
            """
            check for exisiting trades of the same strategy and ticker first,
            if there are none, create a new trade
            if it already exists, add the amount bought (bot will assume 1 share bought each time)
            """

            #check for existing open positions with same strategy and ticker
            existing_open_position = db.query(Trade).filter(
                Trade.ticker == tradeSignal.ticker,
                Trade.strategy == tradeSignal.strategy,
                Trade.quantity > 0
            ).first()

            #if there is no open position, add the trade
            if existing_open_position is None:
                # this creates a trade
                trade = Trade(
                    ticker = tradeSignal.ticker,
                    avg_buy_price = tradeSignal.price, #change here
                    open_time = tradeSignal.time,
                    strategy = tradeSignal.strategy,
                    quantity = 1,
                    total_value = tradeSignal.price
                )

                #this is so in buy below, there will be an existing trade.id
                db.add(trade)
                db.flush()

                buy = Buy(
                    trade_id = trade.id,
                    buy_price = tradeSignal.price,
                    buy_time = tradeSignal.time
                )

            else:

                trade = existing_open_position

                #atomic sql updates to handle requests that come at the same time
                db.execute(
                    update(Trade)
                    .where(Trade.id == trade.id)
                    .values(
                        quantity=Trade.quantity + 1,
                        total_value=Trade.total_value + signal.price,
                        avg_buy_price=(Trade.total_value + signal.price) / (Trade.quantity + 1)
                    )
                )
                
                buy = Buy(
                    trade_id = existing_open_position.id,
                    buy_price = tradeSignal.price,
                    buy_time = tradeSignal.time
                )

            db.add(buy)
            #commit at the end to take note of partial integration issues
            db.commit()
            db.refresh(trade)

            return trade

        except Exception:
            db.rollback()
            raise


       

    if tradeSignal.action == 'sell':
        try:
            #check for existing open positions with same strategy and ticker
            existing_open_position = db.query(Trade).filter(
                Trade.ticker == tradeSignal.ticker,
                Trade.strategy == tradeSignal.strategy,
                Trade.quantity > 0
            ).first()

            if existing_open_position is None:
                raise HTTPException(
                    status_code=409,
                    detail="No open positions to sell"
                )

            #update quantity with concurrency in mind
            sold_state = db.execute(
                update(Trade)
                .where(
                    Trade.id == existing_open_position.id,
                    Trade.quantity > 0
                ).values(
                    quantity=0,
                    sell_price=tradeSignal.price,
                    sell_time=tradeSignal.time,
                    pnl=tradeSignal.price * Trade.quantity - Trade.total_value
                )
            )
            if sold_state.rowcount == 0:
                db.rollback()
                raise HTTPException(
                    status_code=409,
                    detail="Position already closed or does not exist"
                )
            
            db.commit()           # Persist the SELL details and realized P&L.
            db.refresh(existing_open_position)

            return existing_open_position
        
        except Exception:
            db.rollback()
            raise



# Return a list because the endpoint can contain zero, one, or many trades.
@app.get("/920bot/log", response_model=list[ReturnTrade])
def read_trade(db: Session = Depends(get_db)):

    trade_log = []

    # .all() executes the SELECT and returns the rows as Trade objects.
    trades = ( 
        db.query(Trade).all())
    
    for trade in trades:
        # Convert each database row into the public response shape.
        # FastAPI then serializes these models to JSON for the caller.
        return_trade = ReturnTrade(
            id = trade.id, 
            ticker = trade.ticker, 
            avg_buy_price = trade.avg_buy_price, 
            open_time = trade.open_time, 
            sell_price = trade.sell_price,
            sell_time = trade.sell_time, 
            pnl = trade.pnl,
            strategy = trade.strategy,
            total_value = trade.total_value,
            quantity = trade.quantity
            )
        
        trade_log.append(return_trade)
    
    return trade_log

# Return realized earnings: open trades have no P&L yet, so they are excluded.
@app.get("/920bot/earnings", response_model=ReturnEarning)
def read_earnings(db: Session = Depends(get_db)):

    trades = ( 
        db.query(Trade).all())

    total_earnings = 0
    returnEarning = 0
    
    for trade in trades:
        if trade.pnl is None:
            # No SELL has closed this trade yet.
            continue

        total_earnings += trade.pnl

    returnEarning = ReturnEarning(
        earnings = total_earnings)

    return returnEarning

#GET - Return Winrate (Trivial, to be added)
