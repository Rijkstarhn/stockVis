from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EtfCacheMeta(Base):
    __tablename__ = "etf_cache_meta"

    ticker: Mapped[str] = mapped_column(String(16), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    holdings_count: Mapped[int] = mapped_column(Integer, nullable=False)
    data_as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class EtfConstituent(Base):
    __tablename__ = "etf_constituents"
    __table_args__ = (UniqueConstraint("etf_ticker", "stock_ticker", name="uq_etf_stock"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    etf_ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    stock_ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    stock_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weight_percent: Mapped[float] = mapped_column(Float, nullable=False)
