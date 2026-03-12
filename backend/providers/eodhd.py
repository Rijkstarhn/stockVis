import os
from dataclasses import dataclass
from datetime import date

import httpx

BASE_URL = "https://eodhd.com/api/fundamentals/{symbol}.US"
EOD_PRICE_URL = "https://eodhd.com/api/eod/{symbol}.US"


@dataclass
class HoldingRecord:
    stock_ticker: str
    stock_name: str | None
    weight_percent: float


@dataclass
class EtfHoldingsPayload:
    etf_ticker: str
    holdings: list[HoldingRecord]
    holdings_count: int
    data_as_of_date: date | None


@dataclass
class PriceQuote:
    ticker: str
    price: float
    price_date: date


class EodhdProvider:
    def __init__(self, api_key: str | None = None, timeout_seconds: float = 20.0) -> None:
        self.api_key = api_key or os.getenv("EODHD_API_KEY", "demo")
        self.timeout_seconds = timeout_seconds

    def get_etf_holdings(self, etf_ticker: str) -> EtfHoldingsPayload:
        symbol = etf_ticker.upper()
        url = BASE_URL.format(symbol=symbol)
        params = {"api_token": self.api_key, "fmt": "json"}

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(url, params=params)

        if response.status_code != 200:
            raise RuntimeError(f"EODHD request failed ({response.status_code}) for {symbol}")

        if response.text.startswith("Forbidden"):
            raise RuntimeError(f"EODHD access denied for {symbol}.US with current API key")

        payload = response.json()
        etf_data = payload.get("ETF_Data") or {}
        raw_holdings = etf_data.get("Holdings") or {}

        holdings: list[HoldingRecord] = []
        for item in raw_holdings.values():
            stock_ticker = (item.get("Code") or "").strip().upper()
            if not stock_ticker:
                continue
            stock_name = item.get("Name")
            weight_value = item.get("Assets_%")
            try:
                weight_percent = float(weight_value)
            except (TypeError, ValueError):
                continue
            holdings.append(
                HoldingRecord(
                    stock_ticker=stock_ticker,
                    stock_name=stock_name,
                    weight_percent=weight_percent,
                )
            )

        holdings_count = int(etf_data.get("Holdings_Count") or len(holdings))

        # EODHD ETF_Data payload currently does not provide a clear holdings "as-of" date.
        data_as_of_date: date | None = None

        return EtfHoldingsPayload(
            etf_ticker=symbol,
            holdings=holdings,
            holdings_count=holdings_count,
            data_as_of_date=data_as_of_date,
        )

    def get_latest_price(self, ticker: str) -> PriceQuote:
        symbol = ticker.upper()
        url = EOD_PRICE_URL.format(symbol=symbol)
        params = {"api_token": self.api_key, "fmt": "json", "order": "d", "limit": 1}

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(url, params=params)

        if response.status_code != 200:
            raise RuntimeError(f"EODHD price request failed ({response.status_code}) for {symbol}")

        if response.text.startswith("Forbidden"):
            raise RuntimeError(f"EODHD price access denied for {symbol}.US with current API key")

        payload = response.json()
        if not isinstance(payload, list) or not payload:
            raise RuntimeError(f"EODHD price payload missing latest row for {symbol}")

        latest_row = payload[0]
        close_value = latest_row.get("adjusted_close", latest_row.get("close"))
        price_date = latest_row.get("date")

        try:
            price = float(close_value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"EODHD price payload has invalid close for {symbol}") from exc

        if not price_date:
            raise RuntimeError(f"EODHD price payload missing date for {symbol}")

        return PriceQuote(
            ticker=symbol,
            price=price,
            price_date=date.fromisoformat(price_date),
        )
