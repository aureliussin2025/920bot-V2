"""API tests for the multi-buy, multi-ticker, multi-strategy trade flow."""


def signal(
    key: int,
    action: str,
    price: float,
    *,
    ticker: str = "ABC",
    strategy: str = "ema-cross",
    time: str = "2026-08-28T05:30:00",
):
    """Build a valid TradingView-style request body for a test."""
    return {
        "idempotency_key": key,
        "ticker": ticker,
        "action": action,
        "price": price,
        "time": time,
        "strategy": strategy,
    }


def test_first_buy_creates_open_position(client):
    response = client.post("/920bot/webhook", json=signal(1, "buy", 100))

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "ticker": "ABC",
        "avg_buy_price": 100,
        "open_time": "2026-08-28T05:30:00",
        "sell_price": None,
        "sell_time": None,
        "pnl": None,
        "strategy": "ema-cross",
        "quantity": 1,
        "total_value": 100,
    }


def test_second_buy_updates_same_position_and_average(client):
    first_response = client.post("/920bot/webhook", json=signal(1, "buy", 100))
    second_response = client.post(
        "/920bot/webhook",
        json=signal(2, "buy", 120, time="2026-08-28T05:35:00"),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json() == {
        "id": 1,
        "ticker": "ABC",
        "avg_buy_price": 110,
        "open_time": "2026-08-28T05:30:00",
        "sell_price": None,
        "sell_time": None,
        "pnl": None,
        "strategy": "ema-cross",
        "quantity": 2,
        "total_value": 220,
    }


def test_same_ticker_with_different_strategy_creates_separate_position(client):
    first_response = client.post(
        "/920bot/webhook",
        json=signal(1, "buy", 100, strategy="ema-cross"),
    )
    second_response = client.post(
        "/920bot/webhook",
        json=signal(2, "buy", 105, strategy="rsi"),
    )
    log_response = client.get("/920bot/log")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json()["id"] == 2
    assert log_response.status_code == 200
    assert len(log_response.json()) == 2
    assert {trade["strategy"] for trade in log_response.json()} == {
        "ema-cross",
        "rsi",
    }


def test_different_ticker_with_same_strategy_creates_separate_position(client):
    first_response = client.post(
        "/920bot/webhook",
        json=signal(1, "buy", 100, ticker="ABC"),
    )
    second_response = client.post(
        "/920bot/webhook",
        json=signal(2, "buy", 200, ticker="XYZ"),
    )
    log_response = client.get("/920bot/log")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json()["id"] == 2
    assert log_response.status_code == 200
    assert len(log_response.json()) == 2
    assert {trade["ticker"] for trade in log_response.json()} == {"ABC", "XYZ"}


def test_sell_closes_entire_position_and_calculates_pnl(client):
    first_buy = client.post("/920bot/webhook", json=signal(1, "buy", 100))
    second_buy = client.post(
        "/920bot/webhook",
        json=signal(2, "buy", 120, time="2026-08-28T05:35:00"),
    )
    sell_response = client.post(
        "/920bot/webhook",
        json=signal(3, "sell", 130, time="2026-08-28T05:40:00"),
    )

    assert first_buy.status_code == 201
    assert second_buy.status_code == 201
    assert sell_response.status_code == 201
    assert sell_response.json() == {
        "id": 1,
        "ticker": "ABC",
        "avg_buy_price": 110,
        "open_time": "2026-08-28T05:30:00",
        "sell_price": 130,
        "sell_time": "2026-08-28T05:40:00",
        "pnl": 40,
        "strategy": "ema-cross",
        "quantity": 0,
        "total_value": 220,
    }


def test_sell_without_matching_open_position_is_rejected(client):
    response = client.post("/920bot/webhook", json=signal(1, "sell", 100))

    assert response.status_code == 409
    assert response.json() == {"detail": "No open positions to sell"}


def test_duplicate_signal_is_not_processed_twice(client):
    request_body = signal(1, "buy", 100)

    first_response = client.post("/920bot/webhook", json=request_body)
    duplicate_response = client.post("/920bot/webhook", json=request_body)
    log_response = client.get("/920bot/log")

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 201
    assert duplicate_response.json() == {"status": "duplicate signal"}
    assert len(log_response.json()) == 1
    assert log_response.json()[0]["quantity"] == 1


def test_log_is_empty_without_trades(client):
    response = client.get("/920bot/log")

    assert response.status_code == 200
    assert response.json() == []


def test_earnings_excludes_open_positions_and_sums_closed_positions(client):
    open_trade = client.post(
        "/920bot/webhook",
        json=signal(1, "buy", 50, ticker="OPEN"),
    )
    closed_trade_buy = client.post(
        "/920bot/webhook",
        json=signal(2, "buy", 100, ticker="CLOSED"),
    )
    closed_trade_sell = client.post(
        "/920bot/webhook",
        json=signal(
            3,
            "sell",
            125,
            ticker="CLOSED",
            time="2026-08-28T05:40:00",
        ),
    )
    earnings_response = client.get("/920bot/earnings")

    assert open_trade.status_code == 201
    assert closed_trade_buy.status_code == 201
    assert closed_trade_sell.status_code == 201
    assert earnings_response.status_code == 200
    assert earnings_response.json() == {"earnings": 25}


def test_invalid_request_is_rejected_by_pydantic(client):
    response = client.post(
        "/920bot/webhook",
        json=signal(1, "hold", -10),
    )

    assert response.status_code == 422
