import httpx
import pandas as pd
from typing import Optional, List
from app.schemas.market import (
    QuoteResponse, ChartCandle, ChartResponse,
    SearchResult, NewsItem, IndexQuote, TopMover,
)
import asyncio
import logging
import time

logger = logging.getLogger(__name__)

YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com/",
}


class YFinanceService:
    """Service for fetching market data from Yahoo Finance via direct HTTP requests."""

    INDICES = {
        "^GSPC": ("S&P 500", "SPX"),
        "^IXIC": ("NASDAQ", "NASDAQ"),
        "^DJI": ("DOW 30", "DJI"),
        "^VIX": ("VIX", "VIX"),
    }

    TOP_MOVERS_TICKERS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC",
        "NFLX", "CRM", "ORCL", "ADBE", "PYPL", "COIN", "SQ", "SHOP", "UBER", "ABNB",
        "SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "ARKK", "TSM", "BABA",
    ]

    _semaphore: asyncio.Semaphore = asyncio.Semaphore(2)
    _quote_cache: dict = {}
    _top_movers_cache: tuple = None
    _index_cache: tuple = None
    _CACHE_TTL = 60

    def _is_cache_valid(self, cached: tuple) -> bool:
        return cached is not None and (time.time() - cached[0]) < self._CACHE_TTL

    async def get_quote(self, ticker: str) -> Optional[QuoteResponse]:
        if ticker in self._quote_cache and self._is_cache_valid(self._quote_cache[ticker]):
            return self._quote_cache[ticker][1]

        async with self._semaphore:
            await asyncio.sleep(0.5)
            result = await self._fetch_quote(ticker)
            if result is not None:
                self._quote_cache[ticker] = (time.time(), result)
            return result

    async def _fetch_quote(self, ticker: str) -> Optional[QuoteResponse]:
        """Fetch quote using Yahoo Finance v8 chart API directly."""
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=YAHOO_HEADERS) as client:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    params={"range": "1d", "interval": "5m"},
                )
                if resp.status_code == 429:
                    logger.warning(f"Yahoo Finance rate limited for {ticker}")
                    return None
                if resp.status_code != 200:
                    logger.warning(f"Yahoo Finance returned {resp.status_code} for {ticker}")
                    return None
                data = resp.json()
                result = data.get("chart", {}).get("result", [])
                if not result:
                    return None
                meta = result[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                if price is None:
                    return None
                return QuoteResponse(
                    ticker=ticker.upper(),
                    name=meta.get("shortName", meta.get("symbol", ticker)),
                    price=price,
                    change=meta.get("regularMarketChange", 0),
                    change_pct=meta.get("regularMarketChangePercent", 0),
                    high=meta.get("regularMarketDayHigh", 0),
                    low=meta.get("regularMarketDayLow", 0),
                    open=meta.get("regularMarketOpen", 0),
                    previous_close=meta.get("previousClose", 0),
                    volume=meta.get("regularMarketVolume", 0),
                    market_cap=None,
                    pe_ratio=None,
                    week_52_high=None,
                    week_52_low=None,
                    dividend_yield=None,
                    beta=None,
                )
        except Exception as e:
            logger.warning(f"_fetch_quote({ticker}) failed: {e}")
            return None

    async def _fetch_chart_data(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """Fetch chart data using Yahoo Finance v8 chart API."""
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=YAHOO_HEADERS) as client:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    params={"range": period, "interval": interval},
                )
                if resp.status_code != 200:
                    logger.warning(f"Yahoo Finance chart returned {resp.status_code} for {ticker}")
                    return None
                data = resp.json()
                result = data.get("chart", {}).get("result", [])
                if not result or "indicators" not in result[0]:
                    return None
                quotes = result[0].get("indicators", {}).get("quote", [{}])[0]
                timestamps = result[0].get("timestamp", [])
                if not quotes or not timestamps:
                    return None
                df = pd.DataFrame({
                    "Open": quotes.get("open", []),
                    "High": quotes.get("high", []),
                    "Low": quotes.get("low", []),
                    "Close": quotes.get("close", []),
                    "Volume": quotes.get("volume", []),
                }, index=pd.to_datetime(timestamps, unit="s"))
                return df
        except Exception as e:
            logger.warning(f"_fetch_chart_data({ticker}) failed: {e}")
            return None

    async def get_chart(
        self, ticker: str, period: str = "1mo",
        indicators: Optional[List[str]] = None,
    ) -> Optional[ChartResponse]:
        tf_map = {
            "1D": ("1d", "5m"),
            "1W": ("5d", "15m"),
            "1M": ("1mo", "60m"),
            "3M": ("3mo", "60m"),
            "1Y": ("1y", "1d"),
            "MAX": ("max", "1wk"),
        }
        yf_period, interval = tf_map.get(period, ("1mo", "60m"))
        hist = await self._fetch_chart_data(ticker, yf_period, interval)
        if hist is None or hist.empty:
            return None

        candles = []
        for i in range(len(hist)):
            dt = hist.index[i]
            row = hist.iloc[i]
            try:
                candles.append(ChartCandle(
                    time=int(pd.Timestamp(dt).timestamp()),
                    open=float(row["Open"]) if pd.notna(row["Open"]) else 0,
                    high=float(row["High"]) if pd.notna(row["High"]) else 0,
                    low=float(row["Low"]) if pd.notna(row["Low"]) else 0,
                    close=float(row["Close"]) if pd.notna(row["Close"]) else 0,
                    volume=int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
                ))
            except (KeyError, ValueError):
                continue
        return ChartResponse(ticker=ticker.upper(), candles=candles, indicators={})

    async def search_tickers(self, query: str) -> List[SearchResult]:
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=YAHOO_HEADERS) as client:
                resp = await client.get(
                    "https://query1.finance.yahoo.com/v1/finance/search",
                    params={"q": query, "quotesCount": 8, "newsCount": 0},
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
                return [
                    SearchResult(
                        ticker=r.get("symbol", "").upper(),
                        name=r.get("longname", r.get("shortname", "")),
                        exchange=r.get("exchange", ""),
                        type=r.get("quoteType", "EQUITY"),
                    )
                    for r in data.get("quotes", []) if r.get("symbol")
                ]
        except Exception as e:
            logger.warning(f"search_tickers({query}) failed: {e}")
            return []

    async def get_market_news(self) -> List[NewsItem]:
        return []  # Not implemented via direct HTTP for now

    async def get_index_data(self) -> List[IndexQuote]:
        if self._index_cache and self._is_cache_valid(self._index_cache):
            return self._index_cache[1]

        async def fetch_one(symbol: str, name: str, short: str) -> Optional[IndexQuote]:
            ticker_data = await self.get_quote(symbol)
            if not ticker_data:
                return None
            chart = await self.get_chart(symbol, "1D")
            sparkline = [c.close for c in chart.candles[-20:] if pd.notna(c.close)] if chart else []
            return IndexQuote(
                symbol=short,
                name=name,
                price=ticker_data.price,
                change=ticker_data.change,
                change_pct=ticker_data.change_pct,
                sparkline=sparkline,
            )

        tasks = [
            fetch_one(symbol, name, short)
            for symbol, (name, short) in self.INDICES.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid = [r for r in results if r is not None and not isinstance(r, Exception)]
        self._index_cache = (time.time(), valid)
        return valid

    async def _fetch_ticker_info(self, ticker: str) -> Optional[dict]:
        try:
            ticker_data = await self.get_quote(ticker)
            if not ticker_data:
                return None
            return {
                "ticker": ticker,
                "name": ticker_data.name,
                "price": ticker_data.price,
                "change_pct": ticker_data.change_pct,
                "volume": ticker_data.volume,
            }
        except Exception as e:
            logger.warning(f"_fetch_ticker_info({ticker}) failed: {e}")
            return None

    async def get_top_movers(self) -> dict:
        if self._top_movers_cache and self._is_cache_valid(self._top_movers_cache):
            return self._top_movers_cache[1]

        all_quotes = []
        tickers = list(self.TOP_MOVERS_TICKERS)
        for i in range(0, len(tickers), 5):
            batch = tickers[i:i + 5]
            results = await asyncio.gather(
                *[self._fetch_ticker_info(t) for t in batch],
                return_exceptions=True,
            )
            for r in results:
                if r is not None and not isinstance(r, Exception):
                    all_quotes.append(r)
            if i + 5 < len(tickers):
                await asyncio.sleep(1.0)

        if not all_quotes:
            return {"gainers": [], "losers": [], "most_active": []}

        by_change = sorted(all_quotes, key=lambda x: x["change_pct"], reverse=True)
        gainers = [
            TopMover(ticker=q["ticker"], name=q["name"], price=q["price"],
                     change_pct=q["change_pct"], volume=q["volume"])
            for q in by_change[:10]
        ]
        losers = [
            TopMover(ticker=q["ticker"], name=q["name"], price=q["price"],
                     change_pct=q["change_pct"], volume=q["volume"])
            for q in by_change[-10:][::-1]
        ]
        by_volume = sorted(all_quotes, key=lambda x: x["volume"], reverse=True)
        most_active = [
            TopMover(ticker=q["ticker"], name=q["name"], price=q["price"],
                     change_pct=q["change_pct"], volume=q["volume"])
            for q in by_volume[:10]
        ]
        result = {"gainers": gainers, "losers": losers, "most_active": most_active}
        self._top_movers_cache = (time.time(), result)
        return result


yf_service = YFinanceService()
