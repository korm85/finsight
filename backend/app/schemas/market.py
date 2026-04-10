from pydantic import BaseModel
from typing import List, Optional


class IndexQuote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    sparkline: List[float]


class TopMover(BaseModel):
    ticker: str
    name: str
    price: float
    change_pct: float
    volume: int


class TopMoversResponse(BaseModel):
    gainers: List[TopMover]
    losers: List[TopMover]
    most_active: List[TopMover]


class QuoteResponse(BaseModel):
    ticker: str
    name: str
    price: float
    change: float
    change_pct: float
    high: float
    low: float
    open: float
    previous_close: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None


class ChartCandle(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: int


class ChartResponse(BaseModel):
    ticker: str
    candles: List[ChartCandle]
    indicators: dict


class SearchResult(BaseModel):
    ticker: str
    name: str
    exchange: str
    type: str


class NewsItem(BaseModel):
    title: str
    link: str
    pubDate: str
    source: str
