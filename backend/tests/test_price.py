from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import routers.price as price_router_module
from db import Base
from main import app
from models import PriceCache
from services.price_cache import PriceRefreshResult


def make_testing_session_local():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def test_list_price_options_includes_vti(monkeypatch) -> None:
    engine, testing_session_local = make_testing_session_local()
    try:
        with testing_session_local() as session:
            session.add(
                PriceCache(
                    ticker="VTI",
                    price=287.45,
                    price_date=date(2026, 3, 11),
                    fetched_at=datetime.now(UTC),
                )
            )
            session.commit()

        monkeypatch.setattr(price_router_module, "SessionLocal", testing_session_local)

        client = TestClient(app)
        response = client.get("/prices")

        assert response.status_code == 200
        body = response.json()
        assert body["items"][0]["ticker"] == "VTI"
        assert body["items"][0]["price"] == 287.45
        assert body["items"][0]["price_date"] == "2026-03-11"
    finally:
        engine.dispose()


def test_refresh_one_price_uses_service(monkeypatch) -> None:
    def fake_refresh(*args, **kwargs) -> PriceRefreshResult:
        return PriceRefreshResult(
            ticker="VTI",
            updated=True,
            price=387.45,
            price_date="2026-03-11",
            fetched_at="2026-03-11T10:00:00+00:00",
        )

    monkeypatch.setattr(price_router_module, "refresh_price_cache", fake_refresh)

    client = TestClient(app)
    response = client.post("/prices/VTI/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "VTI"
    assert body["updated"] is True
    assert body["price"] == 387.45
