from fastapi import APIRouter, Query
from sqlalchemy import select

from db import SessionLocal
from models import PriceCache
from schemas import PriceOption, PriceOptionsResponse
from services.etf_cache import SUPPORTED_ETFS
from services.price_cache import refresh_price_cache

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("", response_model=PriceOptionsResponse)
def list_price_options() -> PriceOptionsResponse:
    with SessionLocal() as session:
        rows = session.execute(select(PriceCache)).scalars().all()
        by_ticker = {row.ticker: row for row in rows}

    items: list[PriceOption] = []
    for ticker in SUPPORTED_ETFS:
        cached = by_ticker.get(ticker)
        items.append(
            PriceOption(
                ticker=ticker,
                price=cached.price if cached else None,
                price_date=cached.price_date if cached else None,
                fetched_at=cached.fetched_at if cached else None,
            )
        )

    return PriceOptionsResponse(items=items)


@router.post("/{ticker}/refresh")
def refresh_one_price(
    ticker: str,
    force: bool = Query(default=False, description="Force refresh even if today's price is already cached."),
) -> dict[str, str | bool | float]:
    with SessionLocal() as session:
        result = refresh_price_cache(session, ticker=ticker, force=force)
    return {
        "ticker": result.ticker,
        "updated": result.updated,
        "price": result.price,
        "price_date": result.price_date,
        "fetched_at": result.fetched_at,
    }
