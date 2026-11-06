# StrategyBot

[![API Test](https://github.com/aureliussin2025/920bot-V2/actions/workflows/ci.yml/badge.svg)](https://github.com/aureliussin2025/920bot-V2/actions/workflows/ci.yml)

StrategyBot is a paper-trading backend that receives BUY and SELL alerts from
TradingView, groups repeated BUYs into positions, and calculates realized profit
and loss when a position is closed.

It records simulated trades only and does not place real orders with a broker.

## Features

- Receive TradingView signals through a FastAPI webhook.
- Validate each signal with Pydantic.
- Track separate positions by ticker and strategy.
- Combine multiple BUY signals into one open position.
- Record the price and time of every individual BUY.
- Calculate quantity, total invested value, and average buy price.
- Close the full matching position when a SELL signal arrives.
- Calculate realized P&L as `sell price × quantity - total value`.
- Detect repeated webhook deliveries using an idempotency key.
- View open and completed trades through API endpoints.
- View total realized earnings while excluding open positions.
- View trade activity through a simple read-only dashboard.
- Persist data with SQLAlchemy and SQLite.
- Run with Docker Compose and a persistent database volume.
- Run isolated API tests with pytest and a separate test database.
- Run the test suite automatically with GitHub Actions CI.

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- HTML, CSS, and JavaScript
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
Pydantic validation and duplicate detection
      ↓
Position and trading-state logic
      ↓
SQLAlchemy ORM
      ↓
SQLite database

Browser dashboard
      ↓ GET
Trade log and earnings endpoints
```

Each `Trade` row represents one position for a ticker and strategy. The first
BUY creates the position. Further BUYs update its quantity, total value, and
average price. Each individual BUY is also stored in the `buys` table. A SELL
closes the matching position and records its realized P&L.

## Project Structure

```text
920bot-V2/
├── main.py                  FastAPI routes and trading logic
├── schemas.py               Incoming webhook validation
├── models.py                Database tables and response models
├── db.py                    Database engine and session dependency
├── dashboard.html           Read-only trade dashboard
├── conftest.py              Isolated test database and client fixture
├── test_main.py             API test suite
├── requirements.txt         Python dependencies
├── Dockerfile               API image instructions
├── compose.yaml             API and persistent-volume configuration
└── .github/workflows/ci.yml Automated pytest workflow
```

## API and Dashboard

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/920bot/webhook` | Receive a BUY or SELL signal |
| `GET` | `/920bot/log` | Return open and completed trades |
| `GET` | `/920bot/earnings` | Return total realized P&L |
| `GET` | `/dashboard` | Display the read-only trade dashboard |

The current API paths retain the original `/920bot` prefix.

Open the dashboard at:

```text
http://127.0.0.1:8000/dashboard
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Webhook Request

Example BUY request:

```json
{
  "idempotency_key": 1001,
  "ticker": "AAPL",
  "action": "buy",
  "price": 225.50,
  "time": "2026-08-28T05:30:00",
  "strategy": "ema-cross"
}
```

The action must be either `buy` or `sell`, the price must be greater than zero,
and the idempotency key must uniquely identify the webhook event.

## Position Model

| Field | Description |
|---|---|
| `id` | Server-generated position ID |
| `ticker` | Traded symbol |
| `strategy` | Strategy that generated the position |
| `quantity` | Number of simulated shares currently open |
| `avg_buy_price` | Average price across all BUYs in the position |
| `total_value` | Total simulated amount invested |
| `open_time` | Time of the first BUY |
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

The named Docker volume preserves the SQLite database when the API container is
recreated.

## Testing

The API test suite covers:

- Opening a position with the first BUY.
- Combining multiple BUYs and recalculating average price.
- Separating positions by ticker and strategy.
- Closing a full position and calculating P&L.
- Rejecting a SELL without a matching open position.
- Preventing a duplicate signal from being processed twice.
- Returning empty and populated trade logs.
- Excluding open positions from realized earnings.
- Rejecting invalid requests through Pydantic validation.

Run the tests locally:

```bash
python -m pytest -v test_main.py
```

The `client` fixture overrides the normal database dependency with a separate
`test.db`. Tables are created before each test and dropped afterward so tests do
not depend on one another or write trade data into the application database.

## Continuous Integration

The GitHub Actions workflow runs on every push and pull request. It creates a
clean Ubuntu environment, installs Python 3.12 and the project dependencies, and
runs the pytest suite. The workflow provides CI testing but does not automatically
deploy the application.

## Current Scope and Limitations

- Paper trading only; no broker integration or real orders.
- Each BUY alert represents one simulated share.
- A SELL closes the full matching position.
- P&L does not include fees or slippage.
- SQLite and floating-point values are used for this learning project.
- Simultaneous creation of the first position is not yet protected by a database constraint.
- Ticker and strategy values are not yet normalised for case or whitespace.
- The dashboard is read-only and intentionally simple.
