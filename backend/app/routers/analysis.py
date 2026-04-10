from fastapi import APIRouter, HTTPException
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{ticker}")
async def get_analysis(ticker: str):
    result = await analysis_service.get_analysis(ticker.upper())
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not available for this ticker")
    return result