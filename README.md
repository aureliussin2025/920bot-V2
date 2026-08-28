# 920bot

## Paper-trading signal logger and PnL tracker

## Tech Stack
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Docker
- Docker Compose
- Nginx
- AWS EC2
- TradingView webhooks

## Trading strategy
- Buy when the 9 EMA crosses above the 20 EMA.
- Sell when the 9 EMA crosses below the 20 EMA.
- Close an open position at the configured forced-exit time.
- Only one position can be open at a time.

## Assumptions
- One ticker is being tracked.
- One share is bought per trade.
- Only one position can be open at a time.
- Buy and sell signals arrive in the correct order.
- Every buy is followed by one sell.
- Profit is calculated as sell price - buy price.
- All trades are simulated paper trades.

## Features
- Receive TradingView buy and sell webhooks.
- Validate incoming data using Pydantic.
- Store buy and sell signals using SQLAlchemy.
- Persist SQLite data using a Docker volume.
- View completed trades through a GET endpoint.
- Calculate total paper earnings.
- Run locally using Docker Compose.
- Run continuously on an AWS EC2 instance.
- Forward HTTP traffic to FastAPI using Nginx.

## API endpoints
POST    /920bot/webhook	    Receive buy/sell signal
GET     /920bot/log	        View   completed trades
GET	    /920bot/earnings	View total P&L

## Architecture
TradingView → AWS Security Group → Elastic IP → Nginx → Docker → FastAPI → SQLAlchemy → SQLite Docker volume

## Webhook Data
{
  "ticker": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "price": {{strategy.order.price}}
}



# DEPLOYMENT

## Running Locally

### Requirements

Install:

- Git
- Docker Desktop

### Clone the Repository

```bash
git clone https://github.com/aureliussin2025/920bot.git
cd 920bot
```

### Start the Application

```bash
docker compose config
docker compose up -d --build
```

Open the FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### Check the Container

```bash
docker compose ps
```

### View Logs

```bash
docker compose logs
```

To follow new logs continuously:

```bash
docker compose logs -f
```

Press `Ctrl+C` to stop following the logs. This does not stop the container.

### Stop the Application

```bash
docker compose down
```

The SQLite data remains stored in the Docker volume.

## Data Persistence

The application uses the following database URL inside Docker:

```text
sqlite:////data/database.db
```

The database is stored in a named Docker volume:

```text
920bot-data
```

This allows the data to survive container deletion, rebuilding, and restarting.

Deleting the Docker volume will delete the stored database.

## AWS Deployment

The application is deployed on an Ubuntu AWS EC2 instance.

The deployment uses:

- An Elastic IP for a stable public address.
- A security group to control incoming traffic.
- Nginx to receive HTTP traffic on port 80.
- Docker Compose to run FastAPI.
- A Docker volume to persist SQLite data.
- `restart: unless-stopped` to restart the container after failures or server reboots.

Nginx forwards requests as follows:

```text
Port 80 → Nginx → FastAPI on port 8000
```

TradingView’s webhook IP addresses are allowlisted in the AWS security group.
