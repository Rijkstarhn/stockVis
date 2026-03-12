from datetime import UTC, date, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from db import Base
from models import PriceCache
from providers.eodhd import PriceQuote
from services.price_cache import refresh_price_cache


class FakePriceProvider:
    def __init__(self, quote: PriceQuote) -> None:
        self.quote = quote
        self.calls = 0

    def get_latest_price(self, ticker: str) -> PriceQuote:
        self.calls += 1
        return self.quote


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


def test_refresh_price_skips_when_today_cache_exists() -> None:
    session = make_session()
    try:
        now = datetime.now(UTC)
        session.add(
            PriceCache(
                ticker="VTI",
                price=287.45,
                price_date=now.date(),
                fetched_at=now,
            )
        )
        session.commit()

        provider = FakePriceProvider(PriceQuote(ticker="VTI", price=300.0, price_date=now.date()))
        result = refresh_price_cache(session, ticker="VTI", provider=provider)

        assert result.updated is False
        assert result.price == 287.45
        assert provider.calls == 0
    finally:
        close_session(session)


def test_refresh_price_updates_existing_row_when_stale() -> None:
    session = make_session()
    try:
        old_time = datetime.now(UTC) - timedelta(days=1)
        session.add(
            PriceCache(
                ticker="VTI",
                price=280.0,
                price_date=old_time.date(),
                fetched_at=old_time,
            )
        )
        session.commit()

        provider = FakePriceProvider(
            PriceQuote(ticker="VTI", price=287.45, price_date=datetime.now(UTC).date())
        )
        result = refresh_price_cache(session, ticker="VTI", provider=provider)

        assert result.updated is True
        assert result.price == 287.45
        assert provider.calls == 1

        cached = session.execute(select(PriceCache).where(PriceCache.ticker == "VTI")).scalar_one()
        assert cached.price == 287.45
    finally:
        close_session(session)


def test_refresh_price_inserts_when_missing() -> None:
    session = make_session()
    try:
        provider = FakePriceProvider(
            PriceQuote(ticker="MSFT", price=410.25, price_date=date(2026, 3, 11))
        )
        result = refresh_price_cache(session, ticker="MSFT", provider=provider)

        assert result.updated is True
        cached = session.execute(select(PriceCache).where(PriceCache.ticker == "MSFT")).scalar_one()
        assert cached.price == 410.25
        assert cached.price_date == date(2026, 3, 11)
    finally:
        close_session(session)


def test_refresh_price_force_true_updates_even_when_fresh() -> None:
    session = make_session()
    try:
        now = datetime.now(UTC)
        session.add(
            PriceCache(
                ticker="VTI",
                price=280.0,
                price_date=now.date(),
                fetched_at=now,
            )
        )
        session.commit()

        provider = FakePriceProvider(PriceQuote(ticker="VTI", price=287.45, price_date=now.date()))
        result = refresh_price_cache(session, ticker="VTI", provider=provider, force=True)

        assert result.updated is True
        assert provider.calls == 1
    finally:
        close_session(session)
