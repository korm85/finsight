import yfinance as yf
import pandas as pd
from typing import Optional, List
from app.schemas.market import (
    QuoteResponse, ChartCandle, ChartResponse,
    SearchResult, NewsItem, IndexQuote, TopMover,
)
import asyncio


class YFinanceService:
    """Service for fetching market data from Yahoo Finance."""

    INDICES = {
        "^GSPC": ("S&P 500", "SPX"),
        "^IXIC": ("NASDAQ", "NASDAQ"),
        "^DJI": ("DOW 30", "DJI"),
        "^VIX": ("VIX", "VIX"),
    }

    async def get_quote(self, ticker: str) -> Optional[QuoteResponse]:
        try:
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, lambda: yf.Ticker(ticker).info)
            if not stock or "regularMarketPrice" not in stock:
                return None

            return QuoteResponse(
                ticker=ticker.upper(),
                name=stock.get("longName", stock.get("shortName", ticker)),
                price=stock.get("regularMarketPrice", 0),
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
        except Exception:
            return None

    async def get_chart(
        self, ticker: str, period: str = "1mo",
        indicators: Optional[List[str]] = None,
    ) -> Optional[ChartResponse]:
        try:
            loop = asyncio.get_event_loop()
            # Map frontend timeframes to yfinance period + interval
            tf_map = {
                "1D": ("1d", "5m"),
                "1W": ("5d", "15m"),
                "1M": ("1mo", "60m"),
                "3M": ("3mo", "60m"),
                "1Y": ("1y", "1d"),
                "MAX": ("max", "1wk"),
            }
            yf_period, interval = tf_map.get(period, ("1mo", "60m"))

            def _fetch():
                # Use yf.download for better thread safety
                import pandas as pd
                import yfinance as yf_lib
                data = yf_lib.download(
                    ticker,
                    period=yf_period,
                    interval=interval,
                    progress=False,
                    threads=True,
                )
                # Flatten MultiIndex columns from yf.download — keep attribute level
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.droplevel(1)
                return data

            hist = await loop.run_in_executor(None, _fetch)
            if hist is None or hist.empty:
                return None

            # Reset index to get datetime as a column for reliable access
            hist = hist.reset_index()
            candles = [
                ChartCandle(
                    time=int(pd.to_datetime(row['Datetime']).timestamp()),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                )
                for row in hist.to_dict("records")
            ]
            return ChartResponse(ticker=ticker.upper(), candles=candles, indicators={})
        except Exception:
            return None

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
        except Exception:
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
        except Exception:
            return []

    async def get_index_data(self) -> List[IndexQuote]:
        results = []
        for symbol, (name, short) in self.INDICES.items():
            try:
                ticker = await self.get_quote(symbol)
                if ticker:
                    hist = await self.get_chart(symbol, "1D")
                    sparkline = (
                        [c.close for c in hist.candles[-20:]] if hist else []
                    )
                    results.append(IndexQuote(
                        symbol=short,
                        name=name,
                        price=ticker.price,
                        change=ticker.change,
                        change_pct=ticker.change_pct,
                        sparkline=sparkline,
                    ))
            except Exception:
                continue
        return results

    async def get_top_movers(self) -> dict:
        try:
            loop = asyncio.get_event_loop()

            # Popular tickers to evaluate for top movers
            ticker_list = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC",
                "NFLX", "CRM", "ORCL", "ADBE", "PYPL", "COIN", "SQ", "SHOP", "UBER", "ABNB",
                "SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "ARKK", "TSM", "BABA",
            ]

            def fetch():
                quotes = []
                for t in ticker_list:
                    try:
                        info = yf.Ticker(t).info
                        if info and "regularMarketPrice" in info:
                            quotes.append({
                                "ticker": t,
                                "name": info.get("shortName", info.get("longName", t)),
                                "price": info.get("regularMarketPrice", 0),
                                "change_pct": info.get("regularMarketChangePercent", 0),
                                "volume": info.get("regularMarketVolume", 0),
                            })
                    except Exception:
                        continue
                return quotes

            quotes = await loop.run_in_executor(None, fetch)

            # Sort by change_pct
            by_change = sorted(quotes, key=lambda x: x["change_pct"], reverse=True)
            gainers = [
                {"ticker": q["ticker"], "name": q["name"], "price": q["price"],
                 "change_pct": q["change_pct"], "volume": q["volume"]}
                for q in by_change[:10]
            ]
            losers = [
                {"ticker": q["ticker"], "name": q["name"], "price": q["price"],
                 "change_pct": q["change_pct"], "volume": q["volume"]}
                for q in by_change[-10:][::-1]
            ]
            by_volume = sorted(quotes, key=lambda x: x["volume"], reverse=True)
            most_active = [
                {"ticker": q["ticker"], "name": q["name"], "price": q["price"],
                 "change_pct": q["change_pct"], "volume": q["volume"]}
                for q in by_volume[:10]
            ]
            return {"gainers": gainers, "losers": losers, "most_active": most_active}
        except Exception:
            return {"gainers": [], "losers": [], "most_active": []}


yf_service = YFinanceService()