import yfinance as yf
import pandas as pd
from typing import Optional, List
from app.schemas.market import (
    QuoteResponse, ChartCandle, ChartResponse,
    SearchResult, NewsItem, IndexQuote, TopMover,
)
import asyncio
import logging

logger = logging.getLogger(__name__)


class YFinanceService:
    """Service for fetching market data from Yahoo Finance."""

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

    async def get_quote(self, ticker: str) -> Optional[QuoteResponse]:
        try:
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, lambda: yf.Ticker(ticker).info)
            if not stock:
                return None

            price = stock.get("regularMarketPrice") or stock.get("currentPrice")
            if not price:
                return None

            return QuoteResponse(
                ticker=ticker.upper(),
                name=stock.get("longName", stock.get("shortName", ticker)),
                price=price,
                change=stock.get("regularMarketChange", 0),
                change_pct=stock.get("regularMarketChangePercent", 0),
                high=stock.get("regularMarketDayHigh", 0),
                low=stock.get("regularMarketDayLow", 0),
                open=stock.get("regularMarketOpen", 0),
                previous_close=stock.get("regularMarketPreviousClose", 0),
                volume=stock.get("regularMarketVolume", 0),
                market_cap=stock.get("marketCap"),
                pe_ratio=stock.get("trailingPE"),
                week_52_high=stock.get("fiftyTwoWeekHigh"),
                week_52_low=stock.get("fiftyTwoWeekLow"),
                dividend_yield=stock.get("dividendYield"),
                beta=stock.get("beta"),
            )
        except Exception as e:
            logger.warning(f"get_quote({ticker}) failed: {e}")
            return None

    async def _fetch_chart(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        try:
            loop = asyncio.get_event_loop()
            def _fetch():
                data = yf.download(
                    ticker,
                    period=period,
                    interval=interval,
                    progress=False,
                    threads=True,
                )
                if isinstance(data.columns, pd.MultiIndex):
                    data = data.droplevel(1, axis=1)
                return data if data is not None and not data.empty else None
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            logger.warning(f"_fetch_chart({ticker}) failed: {e}")
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
        hist = await self._fetch_chart(ticker, yf_period, interval)
        if hist is None or hist.empty:
            return None

        hist = hist.reset_index()
        candles = []
        for _, row in hist.iterrows():
            dt = row.get("Datetime") or row.get("Date")
            if dt is None:
                continue
            candles.append(ChartCandle(
                time=int(pd.to_datetime(dt).timestamp()),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"]),
            ))
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
        """Parallel fetch for all market indices."""
        async def fetch_one(symbol: str, name: str, short: str) -> Optional[IndexQuote]:
            ticker = await self.get_quote(symbol)
            if not ticker:
                return None
            chart = await self.get_chart(symbol, "1D")
            sparkline = [c.close for c in chart.candles[-20:]] if chart else []
            return IndexQuote(
                symbol=short,
                name=name,
                price=ticker.price,
                change=ticker.change,
                change_pct=ticker.change_pct,
                sparkline=sparkline,
            )

        tasks = [
            fetch_one(symbol, name, short)
            for symbol, (name, short) in self.INDICES.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if r is not None and not isinstance(r, Exception)]

    async def _fetch_ticker_info(self, ticker: str) -> Optional[dict]:
        """Fetch info for a single ticker."""
        try:
            loop = asyncio.get_event_loop()
            def _fetch():
                info = yf.Ticker(ticker).info
                if not info:
                    return None
                price = info.get("regularMarketPrice") or info.get("currentPrice")
                if not price and price != 0:
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
        """Parallel fetch for all top mover tickers."""
        results = await asyncio.gather(
            *[self._fetch_ticker_info(t) for t in self.TOP_MOVERS_TICKERS],
            return_exceptions=True,
        )
        quotes = [r for r in results if r is not None and not isinstance(r, Exception)]

        if not quotes:
            return {"gainers": [], "losers": [], "most_active": []}

        by_change = sorted(quotes, key=lambda x: x["change_pct"], reverse=True)
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
        by_volume = sorted(quotes, key=lambda x: x["volume"], reverse=True)
        most_active = [
            TopMover(ticker=q["ticker"], name=q["name"], price=q["price"],
                     change_pct=q["change_pct"], volume=q["volume"])
            for q in by_volume[:10]
        ]
        return {"gainers": gainers, "losers": losers, "most_active": most_active}


yf_service = YFinanceService()
