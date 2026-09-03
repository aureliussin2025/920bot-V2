# 920bot V2

[![API Test](https://github.com/aureliussin2025/920bot-V2/actions/workflows/ci.yml/badge.svg)](https://github.com/aureliussin2025/920bot-V2/actions/workflows/ci.yml)

A paper-trading backend that receives TradingView BUY and SELL alerts, tracks each
trade from opening to closing, and calculates realized profit and loss.

This project records simulated trades only. It does not place real orders with a
broker.

## Features

- Receive TradingView signals through a FastAPI webhook.
- Validate ticker, action, price, and time using Pydantic.
- Represent a complete BUY-to-SELL lifecycle as one unified trade record.
- Allow only one open position at a time.
- Reject consecutive BUYs, SELLs without an open position, and mismatched tickers.
- Calculate realized P&L as `sell price - buy price` for one simulated share.
- View open and completed trades through a trade-log endpoint.
- View total realized earnings while excluding open positions.
- Persist trade data with SQLAlchemy and SQLite.
- Run locally with Docker Compose and a persistent database volume.
- Run isolated API tests with pytest and a separate SQLite test database.
- Automatically run the test suite on pushes and pull requests with GitHub Actions.

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Pytest and FastAPI TestClient
- Docker and Docker Compose
- GitHub Actions
- TradingView webhooks

## Architecture

```text
TradingView alert
      ↓ POST
FastAPI webhook
      ↓
Pydantic validation and trading rules
      ↓
SQLAlchemy ORM
      ↓
SQLite database
```

Each database row represents one trade. A BUY creates an open row; the matching
SELL updates that row with its sell price, sell time, and realized P&L.

## Project Structure

```text
920bot-V2/
├── main.py                  FastAPI endpoints and trading rules
├── schemas.py               Incoming webhook validation
├── models.py                SQLAlchemy trade model and response models
├── db.py                    Database engine and session dependency
├── conftest.py              Isolated test database and client fixture
├── test_main.py             API test suite
├── requirements.txt         Python dependencies
├── Dockerfile               API image instructions
├── compose.yaml             Local API and persistent volume setup
└── .github/workflows/ci.yml Automated pytest workflow
```

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/920bot/webhook` | Receive a BUY or SELL signal |
| `GET` | `/920bot/log` | Return open and completed trades |
| `GET` | `/920bot/earnings` | Return total realized P&L |

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Webhook Request

Example BUY request:

```json
{
  "ticker": "AAPL",
  "action": "buy",
  "price": 225.50,
  "time": "2026-08-28T05:30:00"
}
```

The action must be either `buy` or `sell`, and the price must be greater than
zero.

## Trade Model

| Field | Description |
|---|---|
| `id` | Server-generated trade ID |
| `ticker` | Traded symbol |
| `buy_price` | Opening price |
| `buy_time` | Opening time |
| `sell_price` | Closing price, or `null` while open |
| `sell_time` | Closing time, or `null` while open |
| `pnl` | Realized P&L, or `null` while open |

## Run Locally

Clone the repository:

```bash
git clone https://github.com/aureliussin2025/920bot-V2.git
cd 920bot-V2
```

Install the dependencies and start FastAPI:

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Alternatively, run it with Docker Compose:

```bash
docker compose up -d --build
```

Stop the containers with:

```bash
docker compose down
```

## Testing

The API test suite covers:

- Opening and closing trades.
- P&L calculation.
- Consecutive BUY rejection.
- SELL rejection when no position is open.
- Empty, open, and completed trade logs.
- Earnings with empty, open, and completed positions.

Run the tests locally:

```bash
python -m pytest -v test_main.py
```

The `client` fixture overrides the production database dependency with a separate
`test.db`. Tables are created before each test and dropped afterward, keeping the
tests independent and preventing test data from entering the application database.

## Continuous Integration

The GitHub Actions workflow runs on every push and pull request. It checks out the
repository, installs Python 3.12 and the project dependencies, and runs the pytest
suite on a clean Ubuntu runner.

## Current Scope

- Paper trading only.
- One simulated share per trade.
- One open position at a time.
- Realized P&L does not include fees or slippage.
