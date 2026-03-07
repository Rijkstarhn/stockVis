from fastapi import APIRouter

from schemas import AnalyzeRequest, AnalyzeResponse
from services.analyze import analyze_portfolio

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return analyze_portfolio(request)
