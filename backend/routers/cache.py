from fastapi import APIRouter, HTTPException

from db import SessionLocal
from schemas import CachePrepareRequest, CachePrepareResponse
from services.cache_prepare import prepare_portfolio_cache

router = APIRouter(prefix="/cache", tags=["cache"])


@router.post("/prepare", response_model=CachePrepareResponse)
def prepare_cache(request: CachePrepareRequest) -> CachePrepareResponse:
    with SessionLocal() as session:
        try:
            return prepare_portfolio_cache(session, request)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
