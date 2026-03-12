from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from db import Base
from models import EtfCacheMeta, EtfConstituent, utcnow
from providers.eodhd import EtfHoldingsPayload, HoldingRecord
from services.etf_cache import _ensure_utc, refresh_etf_cache


class FakeProvider:
    def __init__(self, payload: EtfHoldingsPayload) -> None:
        self.payload = payload
        self.calls = 0

    def get_etf_holdings(self, etf_ticker: str) -> EtfHoldingsPayload:
        self.calls += 1
        return self.payload


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


def test_utcnow_returns_timezone_aware_datetime() -> None:
    assert utcnow().tzinfo is not None


def test_ensure_utc_handles_already_aware_datetime() -> None:
    dt = datetime.now(UTC)
    result = _ensure_utc(dt)
    assert result.tzinfo is not None


def test_refresh_skips_when_cache_is_fresh() -> None:
    session = make_session()
    try:
        now = datetime.now(UTC)
        session.add(
            EtfCacheMeta(
                ticker="VTI",
                provider="eodhd",
                holdings_count=123,
                data_as_of_date=date(2026, 3, 1),
                last_refreshed_at=now,
            )
        )
        session.commit()

        payload = EtfHoldingsPayload(etf_ticker="VTI", holdings=[], holdings_count=999, data_as_of_date=None)
        provider = FakeProvider(payload)
        result = refresh_etf_cache(session, ticker="VTI", provider=provider)

        assert result.updated is False
        assert result.holdings_count == 123
        assert provider.calls == 0
    finally:
        close_session(session)


def test_refresh_updates_stale_cache_and_replaces_constituents() -> None:
    session = make_session()
    try:
        old_time = datetime.now(UTC) - timedelta(days=120)
        session.add(
            EtfCacheMeta(
                ticker="VTI",
                provider="eodhd",
                holdings_count=1,
                data_as_of_date=date(2025, 1, 1),
                last_refreshed_at=old_time,
            )
        )
        session.add(
            EtfConstituent(
                etf_ticker="VTI",
                stock_ticker="OLD",
                stock_name="Old Co",
                weight_percent=1.0,
            )
        )
        session.commit()

        payload = EtfHoldingsPayload(
            etf_ticker="VTI",
            holdings=[
                HoldingRecord(stock_ticker="MSFT", stock_name="Microsoft", weight_percent=4.2),
                HoldingRecord(stock_ticker="AAPL", stock_name="Apple", weight_percent=3.8),
            ],
            holdings_count=2,
            data_as_of_date=date(2026, 3, 7),
        )
        provider = FakeProvider(payload)
        result = refresh_etf_cache(session, ticker="VTI", provider=provider)

        assert result.updated is True
        assert result.holdings_count == 2
        assert provider.calls == 1

        constituents = session.execute(
            select(EtfConstituent).where(EtfConstituent.etf_ticker == "VTI")
        ).scalars().all()
        assert sorted([c.stock_ticker for c in constituents]) == ["AAPL", "MSFT"]

        meta = session.get(EtfCacheMeta, "VTI")
        assert meta is not None
        assert meta.holdings_count == 2
        assert meta.data_as_of_date == date(2026, 3, 7)
    finally:
        close_session(session)


def test_refresh_force_true_updates_even_when_fresh() -> None:
    session = make_session()
    try:
        now = datetime.now(UTC)
        session.add(
            EtfCacheMeta(
                ticker="VTI",
                provider="eodhd",
                holdings_count=1,
                data_as_of_date=now.date(),
                last_refreshed_at=now,
            )
        )
        session.commit()

        payload = EtfHoldingsPayload(
            etf_ticker="VTI",
            holdings=[HoldingRecord(stock_ticker="MSFT", stock_name="Microsoft", weight_percent=5.0)],
            holdings_count=1,
            data_as_of_date=now.date(),
        )
        provider = FakeProvider(payload)
        result = refresh_etf_cache(session, ticker="VTI", provider=provider, force=True)

        assert result.updated is True
        assert provider.calls == 1
    finally:
        close_session(session)


def test_refresh_inserts_meta_when_missing() -> None:
    session = make_session()
    try:
        payload = EtfHoldingsPayload(
            etf_ticker="VTI",
            holdings=[HoldingRecord(stock_ticker="MSFT", stock_name="Microsoft", weight_percent=5.0)],
            holdings_count=1,
            data_as_of_date=date(2026, 3, 7),
        )
        provider = FakeProvider(payload)
        result = refresh_etf_cache(session, ticker="VTI", provider=provider)

        assert result.updated is True
        meta = session.get(EtfCacheMeta, "VTI")
        assert meta is not None
        assert meta.holdings_count == 1
        assert meta.provider == "eodhd"
    finally:
        close_session(session)


def test_refresh_raises_for_unsupported_ticker() -> None:
    session = make_session()
    try:
        payload = EtfHoldingsPayload(etf_ticker="VTI", holdings=[], holdings_count=0, data_as_of_date=None)
        provider = FakeProvider(payload)
        with pytest.raises(ValueError, match="Unsupported ETF"):
            refresh_etf_cache(session, ticker="QQQ", provider=provider)
    finally:
        close_session(session)
