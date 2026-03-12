from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import services.cache_prepare as cache_prepare_module
from db import Base
from schemas import CachePrepareRequest


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


def test_prepare_portfolio_cache_refreshes_etfs_and_prices(monkeypatch) -> None:
    session = make_session()
    try:
        monkeypatch.setattr(
            cache_prepare_module,
            "refresh_etf_cache",
            lambda session, ticker, provider=None, force=False: type(
                "Result",
                (),
                {
                    "ticker": ticker,
                    "updated": True,
                    "holdings_count": 3000,
                    "data_as_of_date": "2026-03-11",
                    "last_refreshed_at": "2026-03-11T10:00:00+00:00",
                },
            )(),
        )
        monkeypatch.setattr(
            cache_prepare_module,
            "refresh_price_cache",
            lambda session, ticker, provider=None, force=False: type(
                "Result",
                (),
                {
                    "ticker": ticker,
                    "updated": True,
                    "price": 100.0,
                    "price_date": "2026-03-11",
                    "fetched_at": "2026-03-11T10:00:00+00:00",
                },
            )(),
        )

        request = CachePrepareRequest(
            holdings=[
                {"ticker": "VTI", "shares": 1},
                {"ticker": "MSFT", "shares": 2},
                {"ticker": "msft", "shares": 3},
            ]
        )

        response = cache_prepare_module.prepare_portfolio_cache(session, request)

        assert [item.ticker for item in response.etfs] == ["VTI"]
        assert [item.ticker for item in response.prices] == ["MSFT", "VTI"]
    finally:
        close_session(session)
