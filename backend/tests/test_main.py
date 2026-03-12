from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import services.analyze as analyze_service
from db import Base
from main import app, create_app
from models import EtfConstituent, PriceCache


def make_testing_session_local():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def seed_price(session, ticker: str, price: float, price_date: date = date(2026, 3, 11)) -> None:
    session.add(
        PriceCache(
            ticker=ticker,
            price=price,
            price_date=price_date,
            fetched_at=datetime.now(UTC),
        )
    )


def test_create_app_metadata() -> None:
    created_app = create_app()
    assert created_app.title == "stockVis API"
    assert created_app.version == "0.1.0"


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint_returns_value_based_rows(monkeypatch) -> None:
    engine, testing_session_local = make_testing_session_local()
    try:
        with testing_session_local() as session:
            seed_price(session, "MSFT", 100.0)
            seed_price(session, "AAPL", 200.0)
            session.commit()

        monkeypatch.setattr(analyze_service, "SessionLocal", testing_session_local)

        client = TestClient(app)
        payload = {
            "holdings": [
                {"ticker": "msft", "shares": 10},
                {"ticker": "AAPL", "shares": 5},
            ],
            "threshold_percent": 1,
        }

        response = client.post("/analyze", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["threshold_percent"] == 1.0
        assert [row["ticker"] for row in body["rows"]] == ["AAPL", "MSFT"]
        assert body["rows"][0]["total_percent"] == 50.0
        assert body["rows"][1]["total_percent"] == 50.0
    finally:
        engine.dispose()


def test_analyze_endpoint_applies_threshold_after_etf_merge(monkeypatch) -> None:
    engine, testing_session_local = make_testing_session_local()
    try:
        with testing_session_local() as session:
            seed_price(session, "VTI", 100.0)
            session.add(
                EtfConstituent(
                    etf_ticker="VTI",
                    stock_ticker="MSFT",
                    stock_name="Microsoft",
                    weight_percent=60.0,
                )
            )
            session.add(
                EtfConstituent(
                    etf_ticker="VTI",
                    stock_ticker="AAPL",
                    stock_name="Apple",
                    weight_percent=40.0,
                )
            )
            session.commit()

        monkeypatch.setattr(analyze_service, "SessionLocal", testing_session_local)

        client = TestClient(app)
        payload = {
            "holdings": [{"ticker": "VTI", "shares": 1}],
            "threshold_percent": 50,
        }

        response = client.post("/analyze", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert [row["ticker"] for row in body["rows"]] == ["MSFT"]
        assert body["rows"][0]["total_percent"] == 60.0
    finally:
        engine.dispose()


def test_analyze_endpoint_returns_409_when_price_cache_missing(monkeypatch) -> None:
    engine, testing_session_local = make_testing_session_local()
    try:
        monkeypatch.setattr(analyze_service, "SessionLocal", testing_session_local)

        client = TestClient(app)
        payload = {
            "holdings": [{"ticker": "MSFT", "shares": 1}],
            "threshold_percent": 1,
        }

        response = client.post("/analyze", json=payload)

        assert response.status_code == 409
        assert response.json() == {"detail": "Missing cached price for MSFT"}
    finally:
        engine.dispose()


def test_analyze_endpoint_returns_409_when_etf_cache_missing(monkeypatch) -> None:
    engine, testing_session_local = make_testing_session_local()
    try:
        with testing_session_local() as session:
            seed_price(session, "VTI", 100.0)
            session.commit()

        monkeypatch.setattr(analyze_service, "SessionLocal", testing_session_local)

        client = TestClient(app)
        payload = {
            "holdings": [{"ticker": "VTI", "shares": 1}],
            "threshold_percent": 1,
        }

        response = client.post("/analyze", json=payload)

        assert response.status_code == 409
        assert response.json() == {"detail": "Missing cached ETF constituents for VTI"}
    finally:
        engine.dispose()
