from services.analyze import analyze_portfolio
from schemas import AnalyzeRequest


def test_aggregates_case_insensitive_tickers() -> None:
    request = AnalyzeRequest(
        holdings=[
            {"ticker": "msft", "shares": 10},
            {"ticker": "MSFT", "shares": 5},
            {"ticker": "AAPL", "shares": 5},
        ],
        threshold_percent=1,
    )

    result = analyze_portfolio(request)

    assert [row.ticker for row in result.rows] == ["MSFT", "AAPL"]
    assert result.rows[0].direct_percent == 75.0
    assert result.rows[1].direct_percent == 25.0


def test_filters_rows_at_threshold() -> None:
    request = AnalyzeRequest(
        holdings=[
            {"ticker": "MSFT", "shares": 10},
            {"ticker": "AAPL", "shares": 5},
            {"ticker": "TSLA", "shares": 5},
        ],
        threshold_percent=30,
    )

    result = analyze_portfolio(request)

    assert [row.ticker for row in result.rows] == ["MSFT"]
    assert result.rows[0].total_percent == 50.0


def test_rows_are_sorted_descending_by_total_percent() -> None:
    request = AnalyzeRequest(
        holdings=[
            {"ticker": "AAPL", "shares": 2},
            {"ticker": "MSFT", "shares": 7},
            {"ticker": "NVDA", "shares": 1},
        ],
        threshold_percent=1,
    )

    result = analyze_portfolio(request)

    totals = [row.total_percent for row in result.rows]
    assert totals == sorted(totals, reverse=True)

import pytest
from types import SimpleNamespace


def test_raises_when_total_shares_zero() -> None:
    request = SimpleNamespace(
        holdings=[SimpleNamespace(ticker="MSFT", shares=0)],
        threshold_percent=1,
    )

    with pytest.raises(ValueError, match="Total shares cannot be zero"):
        analyze_portfolio(request)
