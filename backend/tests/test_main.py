from fastapi.testclient import TestClient

from main import app, create_app


def test_create_app_metadata() -> None:
    created_app = create_app()
    assert created_app.title == "stockVis API"
    assert created_app.version == "0.1.0"


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint_returns_expected_rows() -> None:
    client = TestClient(app)
    payload = {
        "holdings": [
            {"ticker": "msft", "shares": 10},
            {"ticker": "MSFT", "shares": 5},
            {"ticker": "AAPL", "shares": 5},
        ],
        "threshold_percent": 1,
    }

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["threshold_percent"] == 1.0
    assert [row["ticker"] for row in body["rows"]] == ["MSFT", "AAPL"]
    assert body["rows"][0]["total_percent"] == 75.0
    assert body["rows"][1]["total_percent"] == 25.0


def test_analyze_endpoint_applies_threshold() -> None:
    client = TestClient(app)
    payload = {
        "holdings": [
            {"ticker": "MSFT", "shares": 10},
            {"ticker": "AAPL", "shares": 5},
            {"ticker": "TSLA", "shares": 5},
        ],
        "threshold_percent": 30,
    }

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert [row["ticker"] for row in body["rows"]] == ["MSFT"]
    assert body["rows"][0]["total_percent"] == 50.0
