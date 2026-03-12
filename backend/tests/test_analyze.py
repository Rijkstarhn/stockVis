from datetime import UTC, date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db import Base
from models import EtfConstituent, PriceCache
from schemas import AnalyzeRequest
from services.analyze import analyze_portfolio


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    session.info["engine"] = engine
    return session


def close_session(session: Session) -> None:
    engine = session.info.get("engine")
    session.close()
    if engine is not None:
        engine.dispose()


def seed_price(session: Session, ticker: str, price: float, price_date: date = date(2026, 3, 11)) -> None:
    session.add(
        PriceCache(
            ticker=ticker,
            price=price,
            price_date=price_date,
            fetched_at=datetime.now(UTC),
        )
    )


def test_direct_holdings_use_value_based_weighting() -> None:
    session = make_session()
    try:
        seed_price(session, "MSFT", 100.0)
        seed_price(session, "AAPL", 200.0)
        session.commit()

        request = AnalyzeRequest(
            holdings=[
                {"ticker": "msft", "shares": 10},
                {"ticker": "AAPL", "shares": 5},
            ],
            threshold_percent=1,
        )

        result = analyze_portfolio(request, session=session)

        assert [row.ticker for row in result.rows] == ["AAPL", "MSFT"]
        assert result.rows[0].total_percent == 50.0
        assert result.rows[1].total_percent == 50.0
    finally:
        close_session(session)


def test_merges_direct_and_etf_lookthrough_exposure() -> None:
    session = make_session()
    try:
        seed_price(session, "MSFT", 100.0)
        seed_price(session, "VTI", 100.0)
        session.add(
            EtfConstituent(
                etf_ticker="VTI",
                stock_ticker="MSFT",
                stock_name="Microsoft",
                weight_percent=60.0,
            )
        )
        session.add(
            EtfConstituent(
                etf_ticker="VTI",
                stock_ticker="AAPL",
                stock_name="Apple",
                weight_percent=40.0,
            )
        )
        session.commit()

        request = AnalyzeRequest(
            holdings=[
                {"ticker": "VTI", "shares": 1},
                {"ticker": "MSFT", "shares": 1},
            ],
            threshold_percent=1,
        )

        result = analyze_portfolio(request, session=session)

        assert [row.ticker for row in result.rows] == ["MSFT", "AAPL"]
        assert result.rows[0].direct_percent == 50.0
        assert result.rows[0].from_etf_percent == 30.0
        assert result.rows[0].total_percent == 80.0
        assert result.rows[1].direct_percent == 0.0
        assert result.rows[1].from_etf_percent == 20.0
        assert result.rows[1].total_percent == 20.0
    finally:
        close_session(session)


def test_threshold_filters_after_value_based_merge() -> None:
    session = make_session()
    try:
        seed_price(session, "VTI", 100.0)
        session.add(
            EtfConstituent(
                etf_ticker="VTI",
                stock_ticker="MSFT",
                stock_name="Microsoft",
                weight_percent=60.0,
            )
        )
        session.add(
            EtfConstituent(
                etf_ticker="VTI",
                stock_ticker="AAPL",
                stock_name="Apple",
                weight_percent=40.0,
            )
        )
        session.commit()

        request = AnalyzeRequest(
            holdings=[{"ticker": "VTI", "shares": 1}],
            threshold_percent=50,
        )

        result = analyze_portfolio(request, session=session)

        assert [row.ticker for row in result.rows] == ["MSFT"]
        assert result.rows[0].total_percent == 60.0
    finally:
        close_session(session)


def test_raises_when_cached_price_is_missing() -> None:
    session = make_session()
    try:
        request = AnalyzeRequest(
            holdings=[{"ticker": "MSFT", "shares": 1}],
            threshold_percent=1,
        )

        with pytest.raises(ValueError, match="Missing cached price for MSFT"):
            analyze_portfolio(request, session=session)
    finally:
        close_session(session)


def test_raises_when_etf_constituents_are_missing() -> None:
    session = make_session()
    try:
        seed_price(session, "VTI", 100.0)
        session.commit()

        request = AnalyzeRequest(
            holdings=[{"ticker": "VTI", "shares": 1}],
            threshold_percent=1,
        )

        with pytest.raises(ValueError, match="Missing cached ETF constituents for VTI"):
            analyze_portfolio(request, session=session)
    finally:
        close_session(session)


def test_raises_when_total_portfolio_value_is_zero() -> None:
    session = make_session()
    try:
        seed_price(session, "MSFT", 0.0)
        session.commit()

        request = AnalyzeRequest(
            holdings=[{"ticker": "MSFT", "shares": 1}],
            threshold_percent=1,
        )

        with pytest.raises(ValueError, match="Total portfolio value cannot be zero"):
            analyze_portfolio(request, session=session)
    finally:
        close_session(session)
