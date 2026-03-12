from fastapi import APIRouter, HTTPException

from schemas import AnalyzeRequest, AnalyzeResponse
from services.analyze import analyze_portfolio

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze_portfolio(request)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
