from fastapi import APIRouter, Query
from typing import Optional
from fastapi import HTTPException
from app.services.yfinance_service import yf_service
from app.schemas.market import (
    QuoteResponse, ChartResponse, SearchResult, NewsItem,
)

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/overview")
async def get_market_overview() -> dict:
    indices = await yf_service.get_index_data()
    movers = await yf_service.get_top_movers()
    return {"indices": indices, "top_movers": movers}


@router.get("/quote/{ticker}", response_model=QuoteResponse)
async def get_quote(ticker: str):
    quote = await yf_service.get_quote(ticker.upper())
    if not quote:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return quote


@router.get("/chart/{ticker}", response_model=ChartResponse)
async def get_chart(
    ticker: str,
    range: str = Query("1M", pattern="^(1D|1W|1M|3M|1Y|MAX)$"),
    indicators: Optional[str] = Query(None),
):
    indicator_list = indicators.split(",") if indicators else []
    chart = await yf_service.get_chart(ticker.upper(), range, indicator_list)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart data not available")
    return chart


@router.get("/search")
async def search_tickers(q: str = Query(..., min_length=1)):
    return await yf_service.search_tickers(q)


@router.get("/news")
async def get_news() -> list[NewsItem]:
    return await yf_service.get_market_news()