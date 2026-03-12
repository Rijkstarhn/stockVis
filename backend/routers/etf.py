from fastapi import APIRouter, Query
from sqlalchemy import select

from db import SessionLocal
from models import EtfCacheMeta
from schemas import EtfOption, EtfOptionsResponse
from services.etf_cache import SUPPORTED_ETFS, refresh_etf_cache

router = APIRouter(prefix="/etfs", tags=["etfs"])


@router.get("", response_model=EtfOptionsResponse)
def list_etf_options() -> EtfOptionsResponse:
    with SessionLocal() as session:
        rows = session.execute(select(EtfCacheMeta)).scalars().all()
        by_ticker = {row.ticker: row for row in rows}

    items: list[EtfOption] = []
    for ticker, name in SUPPORTED_ETFS.items():
        cached = by_ticker.get(ticker)
        items.append(
            EtfOption(
                ticker=ticker,
                name=name,
                holdings_count=cached.holdings_count if cached else None,
                data_as_of_date=cached.data_as_of_date if cached else None,
                last_refreshed_at=cached.last_refreshed_at if cached else None,
            )
        )

    return EtfOptionsResponse(items=items)


@router.post("/{ticker}/refresh")
def refresh_one_etf(
    ticker: str,
    force: bool = Query(default=False, description="Force refresh even if cache is still seasonal-fresh."),
) -> dict[str, str | bool | int]:
    with SessionLocal() as session:
        result = refresh_etf_cache(session, ticker=ticker, force=force)
    return {
        "ticker": result.ticker,
        "updated": result.updated,
        "holdings_count": result.holdings_count,
        "data_as_of_date": result.data_as_of_date,
        "last_refreshed_at": result.last_refreshed_at,
    }
