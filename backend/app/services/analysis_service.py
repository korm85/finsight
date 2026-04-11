import yfinance as yf
import pandas as pd
import asyncio
from typing import Tuple
from app.schemas.analysis import (
    AnalysisResponse, PlainEnglishData, TechnicalData, FundamentalData,
    RSIData, MACDData, MAData,
)


SECTOR_PE_MEDIANS = {
    "Technology": 30.0,
    "Healthcare": 20.0,
    "Financial Services": 12.0,
    "Consumer Cyclical": 25.0,
    "Energy": 10.0,
    "Industrials": 22.0,
    "Utilities": 18.0,
    "Real Estate": 20.0,
    "Materials": 15.0,
    "Communication Services": 22.0,
}


def compute_rsi(prices: pd.Series, period: int = 14) -> Tuple[float, list[float]]:
    """Compute RSI from a series of prices. Returns current RSI value and history."""
    deltas = prices.diff()
    gains = deltas.clip(lower=0)
    losses = (-deltas).clip(lower=0)

    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    history = rsi.dropna().tolist()
    current = float(rsi.iloc[-1]) if not rsi.isna().iloc[-1] else 50.0
    return current, history


def compute_macd(prices: pd.Series) -> Tuple[float, list[float]]:
    """Compute MACD (12/26/9). Returns latest histogram and histogram history."""
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line

    history = histogram.dropna().tolist()
    current = float(histogram.iloc[-1]) if not histogram.isna().iloc[-1] else 0.0
    return current, history


def compute_ma(prices: pd.Series, period: int) -> Tuple[float, bool]:
    """Compute simple moving average. Returns MA value and whether price is above."""
    ma = prices.rolling(window=period).mean()
    current_ma = float(ma.iloc[-1]) if not ma.isna().iloc[-1] else float(prices.iloc[-1])
    above = float(prices.iloc[-1]) > current_ma
    return current_ma, above


class AnalysisService:
    async def get_analysis(self, ticker: str) -> AnalysisResponse | None:
        loop = asyncio.get_event_loop()

        def fetch():
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            hist_6m = yf.download(ticker, period="6mo", interval="1d", progress=False, threads=True)
            hist_12m = yf.download(ticker, period="12mo", interval="1d", progress=False, threads=True)
            return info, hist_6m, hist_12m

        info, hist_6m, hist_12m = await loop.run_in_executor(None, fetch)

        if hist_6m is None or hist_6m.empty:
            return None

        # Flatten columns if MultiIndex
        if isinstance(hist_6m.columns, pd.MultiIndex):
            hist_6m.columns = hist_6m.columns.droplevel(1)
        if hist_12m is not None and not hist_12m.empty and isinstance(hist_12m.columns, pd.MultiIndex):
            hist_12m.columns = hist_12m.columns.droplevel(1)

        closes_6m = hist_6m["Close"]
        closes_12m = hist_12m["Close"] if hist_12m is not None and not hist_12m.empty else closes_6m

        # Compute indicators
        rsi_val, rsi_history = compute_rsi(closes_6m)
        macd_hist, macd_history = compute_macd(closes_6m)
        ma20_val, ma20_above = compute_ma(closes_6m, 20)
        ma50_val, ma50_above = compute_ma(closes_6m, 50)
        ma200_val, ma200_above = compute_ma(closes_12m, 200)

        # RSI signal
        if rsi_val < 30:
            rsi_signal = "oversold"
        elif rsi_val > 70:
            rsi_signal = "overbought"
        else:
            rsi_signal = "neutral"

        # MACD signal
        macd_signal: str
        if len(macd_history) > 2 and macd_history[-1] > 0 and macd_history[-2] <= 0:
            macd_signal = "bullish_cross"
        elif len(macd_history) > 2 and macd_history[-1] < 0 and macd_history[-2] >= 0:
            macd_signal = "bearish_cross"
        elif macd_hist > 0:
            macd_signal = "neutral"
        else:
            macd_signal = "neutral"

        # 52W position
        high_52w = info.get("fiftyTwoWeekHigh")
        low_52w = info.get("fiftyTwoWeekLow")
        current_price = info.get("regularMarketPrice", float(closes_6m.iloc[-1]))
        if high_52w and low_52w and high_52w != low_52w:
            pos_52w = (current_price - low_52w) / (high_52w - low_52w)
        else:
            pos_52w = 0.5

        # Bullish count
        bullish = 0
        if rsi_signal in ("neutral", "oversold"):
            bullish += 1
        if macd_signal in ("bullish_cross", "neutral") and macd_hist > 0:
            bullish += 1
        if ma20_above:
            bullish += 1
        if ma50_above:
            bullish += 1
        if ma200_above:
            bullish += 1
        if pos_52w < 0.7:
            bullish += 1
        total_count = 6

        # Score (0-10)
        score = round((bullish / total_count) * 10, 1)

        # Recommendation
        if score >= 7:
            recommendation = "strong_buy"
        elif score >= 5.5:
            recommendation = "buy"
        elif score >= 4.5:
            recommendation = "hold"
        elif score >= 3:
            recommendation = "sell"
        else:
            recommendation = "strong_sell"

        # Fundamental data
        pe_ratio = info.get("trailingPE")
        beta = info.get("beta")
        dividend = info.get("dividendYield")
        market_cap = info.get("marketCap")
        sector = info.get("sector", "Technology")
        sector_pe = SECTOR_PE_MEDIANS.get(sector, 25.0)

        if pe_ratio and sector_pe:
            if pe_ratio < sector_pe * 0.85:
                pe_verdict = "cheaper_than_avg"
            elif pe_ratio > sector_pe * 1.15:
                pe_verdict = "expensive"
            else:
                pe_verdict = "fair_value"
        else:
            pe_verdict = "fair_value"

        if market_cap:
            if market_cap > 200e9:
                mcap_label = "Mega"
            elif market_cap > 10e9:
                mcap_label = "Large"
            elif market_cap > 2e9:
                mcap_label = "Mid"
            else:
                mcap_label = "Small"
        else:
            mcap_label = None

        beta_verdict: str | None = None
        if beta is not None:
            if beta < 0.9:
                beta_verdict = "low"
            elif beta < 1.3:
                beta_verdict = "medium"
            else:
                beta_verdict = "high"

        if pos_52w < 0.3:
            range_verdict = "near_low"
        elif pos_52w > 0.75:
            range_verdict = "near_high"
        else:
            range_verdict = "mid_range"

        # Generate verdict text
        verdict_parts = []
        if pe_verdict == "cheaper_than_avg":
            verdict_parts.append("cheaper than sector peers")
        elif pe_verdict == "expensive":
            verdict_parts.append("pricier than sector peers")
        else:
            verdict_parts.append("fairly valued vs peers")

        if bullish >= 4:
            verdict_parts.append("strong momentum")
        elif bullish >= 3:
            verdict_parts.append("mixed momentum")

        if range_verdict == "near_high":
            verdict_parts.append("near 52-week high — consider waiting for dip")
        elif range_verdict == "near_low":
            verdict_parts.append("near 52-week low — potential entry point")

        verdict_text = ", ".join(verdict_parts).capitalize()

        # Plain English generation
        trend = "uptrend" if ma50_above else "downtrend"
        trend_adj = "steady " if bullish >= 4 else "weak "
        day_change = info.get("regularMarketChangePercent", 0)

        newbie = (
            f"{ticker} is {'up' if day_change >= 0 else 'down'} "
            f"{abs(day_change):.1f}% today. "
            f"The stock has been in a {trend_adj}{trend} over the recent period. "
            f"RSI at {rsi_val:.0f} means it's {'near overbought territory — caution' if rsi_val > 65 else 'oversold — a potential buying opportunity' if rsi_val < 35 else 'neither overbought nor oversold — room to move'}. "
            f"The MACD is showing a {'bullish' if macd_hist > 0 else 'bearish'} signal."
        )

        basic = (
            f"{ticker} is showing {'bullish' if bullish >= 4 else 'mixed' if bullish >= 3 else 'bearish'} momentum "
            f"with price {'above' if ma20_above else 'below'} its 20-day average. "
            f"RSI at {rsi_val:.0f} ({rsi_signal}) and MACD histogram at {macd_hist:.2f} "
            f"({'bullish' if macd_hist > 0 else 'bearish'}). "
            f"{f'P/E of {pe_ratio:.1f} is below sector average of {sector_pe:.0f}.' if pe_ratio else ''}"
        )

        pro = (
            f"{ticker}: RSI {rsi_val:.1f} ({rsi_signal}), MACD hist {macd_hist:.3f} ({macd_signal}). "
            f"MA20 {ma20_val:.1f} ({'+' if ma20_above else '-'}), MA50 {ma50_val:.1f} ({'+' if ma50_above else '-'}), "
            f"MA200 {ma200_val:.1f} ({'+' if ma200_above else '-'}). "
            f"{bullish}/6 bullish. "
            f"{f'P/E {pe_ratio:.1f} vs sector {sector_pe:.0f} ({pe_verdict}).' if pe_ratio else ''}"
            f"{f' Beta {beta:.2f} ({beta_verdict} vol).' if beta else ''}"
        )

        return AnalysisResponse(
            ticker=ticker.upper(),
            score=score,
            recommendation=recommendation,
            plain_english=PlainEnglishData(newbie=newbie, basic=basic, pro=pro),
            technical=TechnicalData(
                rsi=RSIData(value=round(rsi_val, 1), signal=rsi_signal),
                macd=MACDData(histogram=round(macd_hist, 3), signal=macd_signal),
                ma20=MAData(value=round(ma20_val, 2), above=ma20_above),
                ma50=MAData(value=round(ma50_val, 2), above=ma50_above),
                ma200=MAData(value=round(ma200_val, 2), above=ma200_above),
                fiftytwo_week_position=round(pos_52w, 3),
                bullish_count=bullish,
                total_count=total_count,
            ),
            fundamental=FundamentalData(
                pe_ratio=round(pe_ratio, 1) if pe_ratio is not None else None,
                sector_pe_median=sector_pe,
                pe_verdict=pe_verdict,
                market_cap_label=mcap_label,
                dividend_yield=round(dividend, 4) if dividend is not None else None,
                beta=round(beta, 2) if beta is not None else None,
                beta_verdict=beta_verdict,
                fiftytwo_week_range_verdict=range_verdict,
                verdict_text=verdict_text,
            ),
        )


analysis_service = AnalysisService()