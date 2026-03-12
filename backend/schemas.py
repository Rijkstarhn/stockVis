from datetime import date, datetime

from pydantic import BaseModel, Field


class HoldingInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g., 'AAPL'.")
    shares: int = Field(..., gt=0, description="Number of shares held, must be > 0.")


class AnalyzeRequest(BaseModel):
    holdings: list[HoldingInput] = Field(
        ...,
        min_length=1,
        description="List of user holdings, must contain at least one item.",
    )
    threshold_percent: float = Field(
        ...,
        ge=1,
        le=100,
        description="Minimum exposure percentage to include in results, between 1 and 100.",
    )


class ExposureRow(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g., 'AAPL'.")
    from_etf_percent: float = Field(..., ge=0, description="Exposure percentage from ETFs.")
    direct_percent: float = Field(..., ge=0, description="Direct exposure percentage.")
    total_percent: float = Field(..., ge=0, description="Total exposure percentage (from_etf_percent + direct_percent).")

class AnalyzeResponse(BaseModel):
    threshold_percent: float = Field(..., description="The threshold percent applied in the analysis.")
    rows: list[ExposureRow] = Field(
        ...,
        description="List of exposure rows meeting the threshold criteria, sorted by total_percent desc.",
    )


class EtfOption(BaseModel):
    ticker: str = Field(..., description="ETF ticker symbol.")
    name: str = Field(..., description="Display name for UI dropdown.")
    holdings_count: int | None = Field(default=None, description="Cached constituent count for this ETF.")
    data_as_of_date: date | None = Field(
        default=None,
        description="Date the holdings snapshot represents (if known).",
    )
    last_refreshed_at: datetime | None = Field(
        default=None,
        description="When cache was last refreshed from provider.",
    )


class EtfOptionsResponse(BaseModel):
    items: list[EtfOption] = Field(..., description="Supported ETF options for dropdown.")


class PriceOption(BaseModel):
    ticker: str = Field(..., description="Ticker symbol for stock or ETF.")
    price: float | None = Field(default=None, description="Latest cached price.")
    price_date: date | None = Field(default=None, description="Market date for the cached price.")
    fetched_at: datetime | None = Field(default=None, description="When the price was last fetched.")


class PriceOptionsResponse(BaseModel):
    items: list[PriceOption] = Field(..., description="Cached price metadata for supported tickers.")


class CachePrepareRequest(BaseModel):
    holdings: list[HoldingInput] = Field(
        ...,
        min_length=1,
        description="List of user holdings to prepare cache data for.",
    )


class CachePrepareEtfResult(BaseModel):
    ticker: str = Field(..., description="ETF ticker symbol.")
    updated: bool = Field(..., description="Whether ETF holdings cache was refreshed.")
    holdings_count: int = Field(..., description="Constituent count stored in cache.")
    data_as_of_date: str = Field(..., description="Date the ETF holdings snapshot represents.")
    last_refreshed_at: str = Field(..., description="When ETF holdings were last refreshed.")


class CachePreparePriceResult(BaseModel):
    ticker: str = Field(..., description="Ticker symbol for the cached price.")
    updated: bool = Field(..., description="Whether price cache was refreshed.")
    price: float = Field(..., description="Cached latest price.")
    price_date: str = Field(..., description="Market date for the cached price.")
    fetched_at: str = Field(..., description="When price was fetched.")


class CachePrepareResponse(BaseModel):
    etfs: list[CachePrepareEtfResult] = Field(..., description="ETF holdings refresh results.")
    prices: list[CachePreparePriceResult] = Field(..., description="Price refresh results.")
