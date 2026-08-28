from fastapi import FastAPI, Depends,HTTPException
from schemas import TradeSignal
from sqlalchemy.orm import Session
from db import Base, engine, get_db
from models import Trade, ReturnTrade, ReturnEarning


Base.metadata.create_all(bind=engine)

app = FastAPI()

# POST - Create trade signal
@app.post("/920bot/webhook", status_code=201, response_model=ReturnTrade)
def create_trade(tradeSignal: TradeSignal, db: Session = Depends(get_db)):

    if tradeSignal.action == 'buy':

        #sequence validation
        latest_trade = (
                    db.query(Trade).order_by(Trade.id.desc()).first())

        if latest_trade is None:
            #POST
            trade = Trade(
                ticker = tradeSignal.ticker,
                buy_price = tradeSignal.price,
                buy_time = tradeSignal.time
            )

            db.add(trade)
            db.commit()
            db.refresh(trade)

            return trade

        if latest_trade.pnl is None:
            raise HTTPException(
                status_code=409,
                detail="Only 1 open position at a time"
            )

        #POST
        trade = Trade(
            ticker = tradeSignal.ticker,
            buy_price = tradeSignal.price,
            buy_time = tradeSignal.time
        )

        db.add(trade)
        db.commit()
        db.refresh(trade)

        return trade

    if tradeSignal.action == 'sell':

        #sequence validation
        latest_trade = (
                    db.query(Trade).order_by(Trade.id.desc()).first())

        if latest_trade is None:
            raise HTTPException(
                status_code=409,
                detail="No open positions to sell"
            )

        if latest_trade.pnl is not None:
            raise HTTPException(
                status_code=409,
                detail="No open positions to sell"
            )

        #Ticker validation:
        if tradeSignal.ticker != latest_trade.ticker:
            raise HTTPException(
                status_code=409,
                detail="Invalid ticker"
            )

        #POST        
        latest_trade.sell_price = tradeSignal.price
        latest_trade.sell_time = tradeSignal.time
        latest_trade.pnl = round((tradeSignal.price - latest_trade.buy_price), 2)


        db.add(latest_trade)
        db.commit()
        db.refresh(latest_trade)

        return latest_trade

    return

# GET - Read full trade log
@app.get("/920bot/log", response_model=list[ReturnTrade])
def read_trade(db: Session = Depends(get_db)):

    trade_log = []

    trades = ( 
        db.query(Trade).all())
    
    for trade in trades:
        return_trade = ReturnTrade(
            id = trade.id, 
            ticker = trade.ticker, 
            buy_price = trade.buy_price, 
            buy_time = trade.buy_time, 
            sell_price = trade.sell_price,
            sell_time = trade.sell_time, 
            pnl = trade.pnl)
        trade_log.append(return_trade)
    
    return trade_log

#GET - Return earnings
@app.get("/920bot/earnings", response_model=ReturnEarning)
def read_earnings(db: Session = Depends(get_db)):

    trades = ( 
        db.query(Trade).all())

    total_earnings = 0
    returnEarning = 0
    
    for trade in trades:
        if trade.pnl is None:
            continue

        total_earnings += trade.pnl

    returnEarning = ReturnEarning(
        earnings = total_earnings)

    return returnEarning

#GET - Return Winrate (Trivial, to be added)