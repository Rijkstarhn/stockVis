# Purpose:
# Define API data contracts for portfolio analysis.
# Keep these models transport-focused (request/response only), no DB logic.

# HoldingInput:
# One user-entered position (ticker + shares).
# Validate ticker format and enforce shares > 0.

# AnalyzeRequest:
# Payload for POST /analyze.
# Includes a non-empty holdings list and threshold_percent in [1, 100].

# ExposureRow:
# One output row after look-through aggregation.
# total_percent = from_etf_percent + direct_percent.

# AnalyzeResponse:
# API response for analysis result.
# Returns applied threshold and rows sorted by total_percent desc (service responsibility).
