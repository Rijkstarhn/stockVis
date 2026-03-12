import pytest

from providers.eodhd import EodhdProvider


class FakeResponse:
    def __init__(self, status_code: int, text: str, payload: dict | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


class FakeClient:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str, params: dict) -> FakeResponse:
        return self.response


def test_get_etf_holdings_parses_holdings_dict(monkeypatch) -> None:
    payload = {
        "ETF_Data": {
            "Holdings_Count": 3,
            "Holdings": {
                "MSFT.US": {"Code": "msft", "Name": "Microsoft", "Assets_%": 4.2},
                "AAPL.US": {"Code": "AAPL", "Name": "Apple", "Assets_%": "3.8"},
                "BADWEIGHT.US": {"Code": "NVDA", "Name": "NVIDIA", "Assets_%": "bad"},
                "BAD.US": {"Code": "", "Name": "Bad", "Assets_%": 1.0},
            },
        }
    }

    monkeypatch.setattr(
        "providers.eodhd.httpx.Client",
        lambda timeout: FakeClient(FakeResponse(200, "{}", payload)),
    )

    provider = EodhdProvider(api_key="test")
    result = provider.get_etf_holdings("vti")

    assert result.etf_ticker == "VTI"
    assert result.holdings_count == 3
    assert [h.stock_ticker for h in result.holdings] == ["MSFT", "AAPL"]
    assert [h.weight_percent for h in result.holdings] == [4.2, 3.8]


def test_get_etf_holdings_raises_on_non_200(monkeypatch) -> None:
    monkeypatch.setattr(
        "providers.eodhd.httpx.Client",
        lambda timeout: FakeClient(FakeResponse(500, "err")),
    )

    provider = EodhdProvider(api_key="test")
    with pytest.raises(RuntimeError, match="request failed"):
        provider.get_etf_holdings("VTI")


def test_get_etf_holdings_raises_on_forbidden(monkeypatch) -> None:
    monkeypatch.setattr(
        "providers.eodhd.httpx.Client",
        lambda timeout: FakeClient(FakeResponse(200, "Forbidden. Please contact support")),
    )

    provider = EodhdProvider(api_key="test")
    with pytest.raises(RuntimeError, match="access denied"):
        provider.get_etf_holdings("VTI")
