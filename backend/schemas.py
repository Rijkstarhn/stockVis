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
