from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import PriceCache
from providers.eodhd import EodhdProvider
from services.etf_cache import _ensure_utc


@dataclass
class PriceRefreshResult:
    ticker: str
    updated: bool
    price: float
    price_date: str
    fetched_at: str


def refresh_price_cache(
    session: Session,
    ticker: str,
    provider: EodhdProvider | None = None,
    force: bool = False,
) -> PriceRefreshResult:
    symbol = ticker.upper()
    now = datetime.now(UTC)

    existing = session.execute(select(PriceCache).where(PriceCache.ticker == symbol)).scalar_one_or_none()

    if not force and existing:
        fetched_at = _ensure_utc(existing.fetched_at)
        if existing.price_date == now.date():
            return PriceRefreshResult(
                ticker=symbol,
                updated=False,
                price=existing.price,
                price_date=existing.price_date.isoformat(),
                fetched_at=fetched_at.isoformat(),
            )

    api = provider or EodhdProvider()
    quote = api.get_latest_price(symbol)

    if existing is None:
        existing = PriceCache(
            ticker=symbol,
            price=quote.price,
            price_date=quote.price_date,
            fetched_at=now,
        )
        session.add(existing)
    else:
        existing.price = quote.price
        existing.price_date = quote.price_date
        existing.fetched_at = now

    session.commit()

    return PriceRefreshResult(
        ticker=symbol,
        updated=True,
        price=quote.price,
        price_date=quote.price_date.isoformat(),
        fetched_at=now.isoformat(),
    )
