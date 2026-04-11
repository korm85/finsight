import yfinance as yf
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


class YFinanceService:
    """Yahoo Finance data service with retry, caching, and rate limiting."""

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
            result = await self._retry_quote(ticker, attempt=0)
            if result is not None:
                self._quote_cache[ticker] = (time.time(), result)
            return result

    async def _retry_quote(self, ticker: str, attempt: int) -> Optional[QuoteResponse]:
        max_attempts = 5
        try:
            loop = asyncio.get_event_loop()
            def _fetch():
                # Try yf.Ticker().info first
                try:
                    ticker_obj = yf.Ticker(ticker)
                    info = ticker_obj.info
                    if info and ("regularMarketPrice" in info or "currentPrice" in info):
                        price = info.get("regularMarketPrice") or info.get("currentPrice")
                        if price is not None:
                            return QuoteResponse(
                                ticker=ticker.upper(),
                                name=info.get("longName", info.get("shortName", ticker)),
                                price=price,
                                change=info.get("regularMarketChange", 0),
                                change_pct=info.get("regularMarketChangePercent", 0),
                                high=info.get("regularMarketDayHigh", 0),
                                low=info.get("regularMarketDayLow", 0),
                                open=info.get("regularMarketOpen", 0),
                                previous_close=info.get("regularMarketPreviousClose", 0),
                                volume=info.get("regularMarketVolume", 0),
                                market_cap=info.get("marketCap"),
                                pe_ratio=info.get("trailingPE"),
                                week_52_high=info.get("fiftyTwoWeekHigh"),
                                week_52_low=info.get("fiftyTwoWeekLow"),
                                dividend_yield=info.get("dividendYield"),
                                beta=info.get("beta"),
                            )
                except Exception as e:
                    logger.warning(f"yf.info({ticker}) failed: {e}")

                # Fallback: use yf.download for price data
                data = yf.download(ticker, period="1d", interval="5m", progress=False, threads=True)
                if data is not None and not data.empty:
                    last = data.iloc[-1]
                    return QuoteResponse(
                        ticker=ticker.upper(),
                        name=ticker,
                        price=float(last["Close"]),
                        change=float(last["Close"] - last["Open"]),
                        change_pct=float((last["Close"] - last["Open"]) / last["Open"] * 100) if last["Open"] else 0,
                        high=float(last["High"]),
                        low=float(last["Low"]),
                        open=float(last["Open"]),
                        previous_close=float(last["Open"]),
                        volume=int(last["Volume"]),
                        market_cap=None,
                        pe_ratio=None,
                        week_52_high=None,
                        week_52_low=None,
                        dividend_yield=None,
                        beta=None,
                    )
                return None

            return await loop.run_in_executor(None, _fetch)

        except Exception as e:
            logger.warning(f"_retry_quote({ticker}) attempt {attempt} failed: {e}")
            if attempt < max_attempts - 1:
                wait = min(2 ** attempt * 2 + (time.time() % 1), 30)
                logger.info(f"Retrying {ticker} in {wait:.1f}s (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(wait)
                return await self._retry_quote(ticker, attempt + 1)
            return None

    async def _fetch_chart(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        async with self._semaphore:
            await asyncio.sleep(0.5)
            return await self._retry_chart(ticker, period, interval, attempt=0)

    async def _retry_chart(self, ticker: str, period: str, interval: str, attempt: int) -> Optional[pd.DataFrame]:
        max_attempts = 3
        try:
            loop = asyncio.get_event_loop()
            def _fetch():
                data = yf.download(ticker, period=period, interval=interval, progress=False, threads=True)
                if isinstance(data.columns, pd.MultiIndex):
                    data = data.droplevel(1, axis=1)
                return data if data is not None and not data.empty else None
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            logger.warning(f"_retry_chart({ticker}) attempt {attempt} failed: {e}")
            if attempt < max_attempts - 1:
                wait = 2 ** attempt * 2
                await asyncio.sleep(wait)
                return await self._retry_chart(ticker, period, interval, attempt + 1)
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
        hist = await self._retry_chart(ticker, yf_period, interval)
        if hist is None or hist.empty:
            return None

        candles = []
        for i in range(len(hist)):
            dt = hist.index[i]
            row = hist.iloc[i]
            try:
                candles.append(ChartCandle(
                    time=int(pd.to_datetime(dt).timestamp()),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                ))
            except (KeyError, ValueError):
                continue
        return ChartResponse(ticker=ticker.upper(), candles=candles, indicators={})

    async def search_tickers(self, query: str) -> List[SearchResult]:
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: yf.Search(query).get("quotes", [])[:8],
            )
            return [
                SearchResult(
                    ticker=r.get("symbol", "").upper(),
                    name=r.get("longname", r.get("shortname", "")),
                    exchange=r.get("exchange", ""),
                    type=r.get("quoteType", "EQUITY"),
                )
                for r in results
                if r.get("symbol")
            ]
        except Exception as e:
            logger.warning(f"search_tickers({query}) failed: {e}")
            return []

    async def get_market_news(self) -> List[NewsItem]:
        try:
            loop = asyncio.get_event_loop()
            news = await loop.run_in_executor(
                None,
                lambda: yf.Ticker("^GSPC").news,
            )
            return [
                NewsItem(
                    title=n.get("title", ""),
                    link=n.get("link", ""),
                    pubDate=n.get("pubDate", ""),
                    source=n.get("source", ""),
                )
                for n in (news or [])[:10]
            ]
        except Exception as e:
            logger.warning(f"get_market_news failed: {e}")
            return []

    async def get_index_data(self) -> List[IndexQuote]:
        if self._index_cache and self._is_cache_valid(self._index_cache):
            return self._index_cache[1]

        async def fetch_one(symbol: str, name: str, short: str) -> Optional[IndexQuote]:
            ticker_data = await self.get_quote(symbol)
            if not ticker_data:
                return None
            chart = await self.get_chart(symbol, "1D")
            sparkline = [c.close for c in chart.candles[-20:]] if chart else []
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
            loop = asyncio.get_event_loop()
            def _fetch():
                info = yf.Ticker(ticker).info
                if not info:
                    return None
                price = info.get("regularMarketPrice") or info.get("currentPrice")
                if price is None:
                    return None
                return {
                    "ticker": ticker,
                    "name": info.get("shortName", info.get("longName", ticker)),
                    "price": price,
                    "change_pct": info.get("regularMarketChangePercent", 0),
                    "volume": info.get("regularMarketVolume", 0),
                }
            return await loop.run_in_executor(None, _fetch)
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
                await asyncio.sleep(1.5)

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
