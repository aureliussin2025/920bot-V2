def test_post_buy(client):
    response_body = {
        "ticker": "ABC",
        "action": "buy",
        "price": 100,
        "time": "2026-08-28T05:30:00"
    }

    response = client.post("/920bot/webhook", json=response_body)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "ticker": "ABC",
        "buy_price": 100,
        "buy_time": "2026-08-28T05:30:00",
        "sell_price": None,
        "sell_time": None,
        "pnl": None
    }

def test_post_sell(client):

    response_body1 = {
        "ticker": "ABC",
        "action": "buy",
        "price": 100,
        "time": "2026-08-28T05:30:00"
    }

    response_body2 = {
        "ticker": "ABC",
        "action": "sell",
        "price": 101,
        "time": "2026-08-28T05:35:00"
    }

    response1 = client.post("/920bot/webhook", json=response_body1)
    response2 = client.post("/920bot/webhook", json=response_body2)

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response2.json() == {
        "id": 1,
        "ticker": "ABC",
        "buy_price": 100,
        "buy_time": "2026-08-28T05:30:00",
        "sell_price": 101,
        "sell_time": "2026-08-28T05:35:00",
        "pnl": 1
    }

def test_consecutive_buys(client):

    response_body1 = {
        "ticker": "ABC",
        "action": "buy",
        "price": 100,
        "time": "2026-08-28T05:30:00"
    }

    response_body2 = {
        "ticker": "ABC",
        "action": "buy",
        "price": 100,
        "time": "2026-08-28T05:35:00"
    }

    response1 = client.post("/920bot/webhook", json=response_body1)
    response2 = client.post("/920bot/webhook", json=response_body2)

    assert response1.status_code == 201
    assert response2.status_code == 409
    assert response2.json() == {"detail": "Only 1 open position at a time"}

def test_reject_no_open_position_sells(client):

    response_body = {
        "ticker": "ABC",
        "action": "sell",
        "price": 100,
        "time": "2026-08-28T05:30:00"
    }

    response = client.post("/920bot/webhook", json=response_body)

    assert response.status_code == 409
    assert response.json() == {"detail": "No open positions to sell"}

def test_logs_without_trades(client):

    response = client.get("/920bot/log")

    assert response.status_code == 200
    assert response.json() == []

def test_logs_with_open_positions(client):
    response_body1 = {
        "ticker": "ABC",
        "action": "buy",
        "price": 100,
        "time": "2026-08-28T05:30:00"
    }

    response1 = client.post("/920bot/webhook", json=response_body1)
    response2 = client.get("/920bot/log")

    assert response1.status_code == 201
    assert response2.status_code == 200
    assert response2.json() == [
        {"id": 1, 
        "ticker": "ABC", 
        "buy_price": 100, 
        "buy_time": "2026-08-28T05:30:00", 
        "sell_price": None, 
        "sell_time": None, 
        "pnl": None}
        ]

def test_logs_with_closed_positions(client):
    response_body1 = {
        "ticker": "ABC",
        "action": "buy",
        "price": 100,
        "time": "2026-08-28T05:30:00"
    }

    response_body2 = {
        "ticker": "ABC",
        "action": "sell",
        "price": 101,
        "time": "2026-08-28T05:35:00"
    }

    response1 = client.post("/920bot/webhook", json=response_body1)
    response2 = client.post("/920bot/webhook", json=response_body2)
    response3 = client.get("/920bot/log")

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response3.status_code == 200
    assert response3.json() == [
        {"id": 1, 
        "ticker": "ABC", 
        "buy_price": 100, 
        "buy_time": "2026-08-28T05:30:00", 
        "sell_price": 101, 
        "sell_time": "2026-08-28T05:35:00", 
        "pnl": 1}
        ]

def test_earnings_without_trades(client):

    response = client.get("/920bot/earnings")

    assert response.status_code == 200
    assert response.json() == {"earnings": 0}

def test_earnings_with_open_positions(client):

    response_body1 = {
        "ticker": "ABC",
        "action": "buy",
        "price": 100,
        "time": "2026-08-28T05:30:00"
    }

    response1 = client.post("/920bot/webhook", json=response_body1)
    response2 = client.get("/920bot/earnings")

    assert response1.status_code == 201
    assert response2.status_code == 200
    assert response2.json() == {"earnings": 0}

def test_earnings_without_open_positions(client):

    response_body1 = {
        "ticker": "ABC",
        "action": "buy",
        "price": 100,
        "time": "2026-08-28T05:30:00"
    }

    response_body2 = {
            "ticker": "ABC",
            "action": "sell",
            "price": 101,
            "time": "2026-08-28T05:35:00"
        }

    response1 = client.post("/920bot/webhook", json=response_body1)
    response2 = client.post("/920bot/webhook", json=response_body2)
    response3 = client.get("/920bot/earnings")

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response3.status_code == 200
    assert response3.json() == {"earnings": 1}

