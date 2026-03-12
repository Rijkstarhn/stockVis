from sqlalchemy.orm import Session

from schemas import (
    CachePrepareEtfResult,
    CachePreparePriceResult,
    CachePrepareRequest,
    CachePrepareResponse,
)
from services.etf_cache import SUPPORTED_ETFS, refresh_etf_cache
from services.price_cache import refresh_price_cache


def prepare_portfolio_cache(session: Session, request: CachePrepareRequest) -> CachePrepareResponse:
    unique_tickers = sorted({holding.ticker.upper() for holding in request.holdings})

    etf_results: list[CachePrepareEtfResult] = []
    for ticker in unique_tickers:
        if ticker in SUPPORTED_ETFS:
            result = refresh_etf_cache(session, ticker=ticker)
            etf_results.append(
                CachePrepareEtfResult(
                    ticker=result.ticker,
                    updated=result.updated,
                    holdings_count=result.holdings_count,
                    data_as_of_date=result.data_as_of_date,
                    last_refreshed_at=result.last_refreshed_at,
                )
            )

    price_results: list[CachePreparePriceResult] = []
    for ticker in unique_tickers:
        result = refresh_price_cache(session, ticker=ticker)
        price_results.append(
            CachePreparePriceResult(
                ticker=result.ticker,
                updated=result.updated,
                price=result.price,
                price_date=result.price_date,
                fetched_at=result.fetched_at,
            )
        )

    return CachePrepareResponse(
        etfs=etf_results,
        prices=price_results,
    )
