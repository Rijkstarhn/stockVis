from sqlalchemy import select
from sqlalchemy.orm import Session

from db import SessionLocal
from models import EtfConstituent, PriceCache
from schemas import AnalyzeRequest, AnalyzeResponse, ExposureRow
from services.etf_cache import SUPPORTED_ETFS


def _get_cached_price(session: Session, ticker: str) -> float:
    symbol = ticker.upper()
    cached = session.execute(select(PriceCache).where(PriceCache.ticker == symbol)).scalar_one_or_none()
    if cached is None:
        raise ValueError(f"Missing cached price for {symbol}")
    return cached.price


def _get_etf_constituents(session: Session, ticker: str) -> list[EtfConstituent]:
    symbol = ticker.upper()
    rows = session.execute(
        select(EtfConstituent).where(EtfConstituent.etf_ticker == symbol)
    ).scalars().all()
    if not rows:
        raise ValueError(f"Missing cached ETF constituents for {symbol}")
    return rows


def analyze_portfolio(request: AnalyzeRequest, session: Session | None = None) -> AnalyzeResponse:
    own_session = session is None
    db_session = session or SessionLocal()

    try:
        aggregated_holdings: dict[str, int] = {}
        for holding in request.holdings:
            ticker = holding.ticker.upper()
            aggregated_holdings[ticker] = aggregated_holdings.get(ticker, 0) + holding.shares

        direct_values: dict[str, float] = {}
        etf_values: dict[str, float] = {}
        total_portfolio_value = 0.0

        for ticker, shares in aggregated_holdings.items():
            if ticker in SUPPORTED_ETFS:
                etf_price = _get_cached_price(db_session, ticker)
                etf_total_value = shares * etf_price
                total_portfolio_value += etf_total_value

                for constituent in _get_etf_constituents(db_session, ticker):
                    etf_values[constituent.stock_ticker] = etf_values.get(constituent.stock_ticker, 0.0) + (
                        etf_total_value * constituent.weight_percent / 100.0
                    )
            else:
                stock_price = _get_cached_price(db_session, ticker)
                direct_value = shares * stock_price
                direct_values[ticker] = direct_values.get(ticker, 0.0) + direct_value
                total_portfolio_value += direct_value

        if total_portfolio_value <= 0:
            raise ValueError("Total portfolio value cannot be zero.")

        rows: list[ExposureRow] = []
        for ticker in set(direct_values) | set(etf_values):
            direct_percent = (direct_values.get(ticker, 0.0) / total_portfolio_value) * 100.0
            from_etf_percent = (etf_values.get(ticker, 0.0) / total_portfolio_value) * 100.0
            total_percent = direct_percent + from_etf_percent
            rows.append(
                ExposureRow(
                    ticker=ticker,
                    from_etf_percent=from_etf_percent,
                    direct_percent=direct_percent,
                    total_percent=total_percent,
                )
            )

        filtered_rows = [row for row in rows if row.total_percent >= request.threshold_percent]
        sorted_rows = sorted(filtered_rows, key=lambda row: (-row.total_percent, row.ticker))

        return AnalyzeResponse(
            threshold_percent=request.threshold_percent,
            rows=sorted_rows,
        )
    finally:
        if own_session:
            db_session.close()
