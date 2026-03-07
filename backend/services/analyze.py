from schemas import AnalyzeRequest, AnalyzeResponse, ExposureRow


def analyze_portfolio(request: AnalyzeRequest) -> AnalyzeResponse:
    # Step 1: Aggregate shares by ticker (case-insensitive)
    ticker_shares = {}
    for holding in request.holdings:
        ticker = holding.ticker.upper()  # Normalize to uppercase
        shares = holding.shares
        if ticker in ticker_shares:
            ticker_shares[ticker] += shares
        else:
            ticker_shares[ticker] = shares

    # Step 2: Calculate total shares for percentage calculation
    total_shares = sum(ticker_shares.values())
    if total_shares == 0:
        raise ValueError("Total shares cannot be zero.")

    # Step 3: Create ExposureRow list with calculated percentages
    rows = []
    for ticker, shares in ticker_shares.items():
        direct_percent = (shares / total_shares) * 100
        row = ExposureRow(
            ticker=ticker,
            from_etf_percent=0.0,  # No ETF expansion in v1
            direct_percent=direct_percent,
            total_percent=direct_percent,  # Total is just direct in v1
        )
        rows.append(row)

    # Step 4: Filter rows by threshold_percent
    filtered_rows = [row for row in rows if row.total_percent >= request.threshold_percent]

    # Step 5: Sort rows by total_percent descending
    sorted_rows = sorted(filtered_rows, key=lambda r: r.total_percent, reverse=True)

    # Step 6: Construct and return AnalyzeResponse
    response = AnalyzeResponse(
        threshold_percent=request.threshold_percent,
        rows=sorted_rows,
    )
    return response
