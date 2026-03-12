from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from models import EtfCacheMeta, EtfConstituent
from providers.eodhd import EodhdProvider

SUPPORTED_ETFS: dict[str, str] = {
    "VTI": "Vanguard Total Stock Market ETF",
}
SEASONAL_REFRESH_DAYS = 90


@dataclass
class RefreshResult:
    ticker: str
    updated: bool
    holdings_count: int
    data_as_of_date: str
    last_refreshed_at: str


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def refresh_etf_cache(
    session: Session,
    ticker: str,
    provider: EodhdProvider | None = None,
    force: bool = False,
) -> RefreshResult:
    symbol = ticker.upper()
    if symbol not in SUPPORTED_ETFS:
        raise ValueError(f"Unsupported ETF: {symbol}")

    meta = session.get(EtfCacheMeta, symbol)
    now = datetime.now(UTC)
    stale_before = now - timedelta(days=SEASONAL_REFRESH_DAYS)

    if not force and meta and _ensure_utc(meta.last_refreshed_at) >= stale_before:
        last_refreshed = _ensure_utc(meta.last_refreshed_at)
        data_as_of = meta.data_as_of_date.isoformat() if meta.data_as_of_date else last_refreshed.date().isoformat()
        return RefreshResult(
            ticker=symbol,
            updated=False,
            holdings_count=meta.holdings_count,
            data_as_of_date=data_as_of,
            last_refreshed_at=last_refreshed.isoformat(),
        )

    api = provider or EodhdProvider()
    payload = api.get_etf_holdings(symbol)
    data_as_of = payload.data_as_of_date or now.date()

    session.execute(delete(EtfConstituent).where(EtfConstituent.etf_ticker == symbol))
    session.add_all(
        [
            EtfConstituent(
                etf_ticker=symbol,
                stock_ticker=item.stock_ticker,
                stock_name=item.stock_name,
                weight_percent=item.weight_percent,
            )
            for item in payload.holdings
        ]
    )

    if meta is None:
        meta = EtfCacheMeta(
            ticker=symbol,
            provider="eodhd",
            holdings_count=payload.holdings_count,
            data_as_of_date=data_as_of,
            last_refreshed_at=now,
        )
        session.add(meta)
    else:
        meta.provider = "eodhd"
        meta.holdings_count = payload.holdings_count
        meta.data_as_of_date = data_as_of
        meta.last_refreshed_at = now

    session.commit()

    return RefreshResult(
        ticker=symbol,
        updated=True,
        holdings_count=payload.holdings_count,
        data_as_of_date=data_as_of.isoformat(),
        last_refreshed_at=now.isoformat(),
    )
