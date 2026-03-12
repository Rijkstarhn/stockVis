from fastapi.testclient import TestClient

import routers.etf as etf_router_module
from main import app
from services.etf_cache import RefreshResult


def test_list_etf_options_includes_vti() -> None:
    client = TestClient(app)
    response = client.get("/etfs")

    assert response.status_code == 200
    body = response.json()
    tickers = [item["ticker"] for item in body["items"]]
    assert "VTI" in tickers


def test_refresh_one_etf_uses_service(monkeypatch) -> None:
    def fake_refresh(*args, **kwargs) -> RefreshResult:
        return RefreshResult(
            ticker="VTI",
            updated=True,
            holdings_count=3000,
            data_as_of_date="2026-03-07",
            last_refreshed_at="2026-03-07T10:00:00+00:00",
        )

    monkeypatch.setattr(etf_router_module, "refresh_etf_cache", fake_refresh)

    client = TestClient(app)
    response = client.post("/etfs/VTI/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "VTI"
    assert body["updated"] is True
    assert body["holdings_count"] == 3000
