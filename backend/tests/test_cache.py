from fastapi.testclient import TestClient

import routers.cache as cache_router_module
from main import app
from schemas import CachePrepareResponse


def test_prepare_cache_endpoint_returns_refresh_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        cache_router_module,
        "prepare_portfolio_cache",
        lambda session, request: CachePrepareResponse(
            etfs=[
                {
                    "ticker": "VTI",
                    "updated": True,
                    "holdings_count": 3000,
                    "data_as_of_date": "2026-03-11",
                    "last_refreshed_at": "2026-03-11T10:00:00+00:00",
                }
            ],
            prices=[
                {
                    "ticker": "VTI",
                    "updated": True,
                    "price": 287.45,
                    "price_date": "2026-03-11",
                    "fetched_at": "2026-03-11T10:00:00+00:00",
                },
                {
                    "ticker": "MSFT",
                    "updated": False,
                    "price": 410.25,
                    "price_date": "2026-03-11",
                    "fetched_at": "2026-03-11T08:00:00+00:00",
                },
            ],
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/cache/prepare",
        json={
            "holdings": [
                {"ticker": "VTI", "shares": 1},
                {"ticker": "MSFT", "shares": 2},
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["ticker"] for item in body["etfs"]] == ["VTI"]
    assert [item["ticker"] for item in body["prices"]] == ["VTI", "MSFT"]


def test_prepare_cache_endpoint_returns_409_on_value_error(monkeypatch) -> None:
    def fake_prepare(session, request):
        raise ValueError("Missing cached price for MSFT")

    monkeypatch.setattr(cache_router_module, "prepare_portfolio_cache", fake_prepare)

    client = TestClient(app)
    response = client.post(
        "/cache/prepare",
        json={"holdings": [{"ticker": "MSFT", "shares": 1}]},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Missing cached price for MSFT"}


def test_prepare_cache_endpoint_returns_502_on_runtime_error(monkeypatch) -> None:
    def fake_prepare(session, request):
        raise RuntimeError("EODHD price access denied for NVDA.US with current API key")

    monkeypatch.setattr(cache_router_module, "prepare_portfolio_cache", fake_prepare)

    client = TestClient(app)
    response = client.post(
        "/cache/prepare",
        json={"holdings": [{"ticker": "NVDA", "shares": 1}]},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "EODHD price access denied for NVDA.US with current API key"}
