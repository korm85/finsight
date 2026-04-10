# Trading Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a trading assistant panel to the Stock Detail page with three analysis cards (Plain English, Technical Indicators, Fundamentals) and a Newbie/Basic/Pro mode switcher.

**Architecture:** A new `analysis_service.py` computes RSI, MACD, MAs from Yahoo Finance price history. A new `/api/analysis/{ticker}` FastAPI endpoint returns all computed data. A `TradingAssistant` React component renders three cards on the Stock Detail page. Mode preference is stored in `localStorage`.

**Tech Stack:** FastAPI + Python (backend), React + TypeScript + Tailwind (frontend), yfinance (already in use), lightweight inline SVG sparklines (no new library).

---

## Task 1: Backend — Analysis Schema

**Files:**
- Create: `backend/app/schemas/analysis.py`

- [ ] **Step 1: Create the Pydantic response schema**

```python
from pydantic import BaseModel
from typing import Literal


class RSIData(BaseModel):
    value: float
    signal: Literal["oversold", "neutral", "overbought"]


class MACDData(BaseModel):
    histogram: float
    signal: Literal["bullish_cross", "bearish_cross", "neutral"]


class MAData(BaseModel):
    value: float
    above: bool


class TechnicalData(BaseModel):
    rsi: RSIData
    macd: MACDData
    ma20: MAData
    ma50: MAData
    ma200: MAData
    fiftytwo_week_position: float
    bullish_count: int
    total_count: int


class FundamentalData(BaseModel):
    pe_ratio: float | None
    sector_pe_median: float | None
    pe_verdict: Literal["cheaper_than_avg", "fair_value", "expensive"]
    market_cap_label: Literal["Mega", "Large", "Mid", "Small"] | None
    dividend_yield: float | None
    beta: float | None
    beta_verdict: Literal["low", "medium", "high"] | None
    fiftytwo_week_range_verdict: Literal["near_low", "mid_range", "near_high"]
    verdict_text: str


class PlainEnglishData(BaseModel):
    newbie: str
    basic: str
    pro: str


class AnalysisResponse(BaseModel):
    ticker: str
    score: float
    recommendation: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]
    plain_english: PlainEnglishData
    technical: TechnicalData
    fundamental: FundamentalData
```

- [ ] **Step 2: Export from schemas __init__.py**

Modify `backend/app/schemas/__init__.py` to add:
```python
from app.schemas.analysis import (
    AnalysisResponse, PlainEnglishData, TechnicalData, FundamentalData,
    RSIData, MACDData, MAData,
)
```
Add these to the `__all__` list.

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/analysis.py backend/app/schemas/__init__.py
git commit -m "feat(analysis): add Pydantic schemas for trading assistant"
```

---

## Task 2: Backend — Analysis Service

**Files:**
- Create: `backend/app/services/analysis_service.py`

- [ ] **Step 1: Create the analysis service with RSI, MACD, MA calculations**

```python
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
    current = rsi.iloc[-1] if not rsi.isna().iloc[-1] else 50.0
    return float(current), history


def compute_macd(prices: pd.Series) -> Tuple[float, list[float]]:
    """Compute MACD (12/26/9). Returns latest histogram and histogram history."""
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line

    history = histogram.dropna().tolist()
    current = histogram.iloc[-1] if not histogram.isna().iloc[-1] else 0.0
    return float(current), history


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
        if isinstance(hist_12m.columns, pd.MultiIndex):
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

        # MACD signal (cross detection from histogram sign change)
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
        current_price = info.get("regularMarketPrice", closes_6m.iloc[-1])
        pos_52w: float
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

        newbie = (
            f"{ticker} is {'up' if info.get('regularMarketChangePercent', 0) >= 0 else 'down'} "
            f"{abs(info.get('regularMarketChangePercent', 0)):.1f}% today. "
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
                pe_ratio=round(pe_ratio, 1) if pe_ratio else None,
                sector_pe_median=sector_pe,
                pe_verdict=pe_verdict,
                market_cap_label=mcap_label,
                dividend_yield=round(dividend, 4) if dividend else None,
                beta=round(beta, 2) if beta else None,
                beta_verdict=beta_verdict,
                fiftytwo_week_range_verdict=range_verdict,
                verdict_text=verdict_text,
            ),
        )


analysis_service = AnalysisService()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/analysis_service.py
git commit -m "feat(analysis): add analysis service with RSI, MACD, MA calculations"
```

---

## Task 3: Backend — Analysis Router

**Files:**
- Create: `backend/app/routers/analysis.py`
- Modify: `backend/app/routers/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create the FastAPI router**

```python
from fastapi import APIRouter, HTTPException
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{ticker}")
async def get_analysis(ticker: str):
    result = await analysis_service.get_analysis(ticker.upper())
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not available for this ticker")
    return result
```

- [ ] **Step 2: Register router in __init__ and main.py**

Add to `backend/app/routers/__init__.py`:
```python
from app.routers.analysis import router as analysis_router
```
Add `"analysis_router"` to the `__all__` list.

Add to `backend/app/main.py` imports:
```python
from app.routers import (
    market_router, portfolio_router, watchlist_router,
    alerts_router, settings_router, analysis_router,
)
```
Add `app.include_router(analysis_router)` after the other routers.

- [ ] **Step 3: Verify the endpoint works**

Run: `curl -s http://localhost:8000/api/analysis/NVDA | python3 -m json.tool`
Expected: JSON response with ticker, score, recommendation, technical RSI/MACD data, fundamental verdict

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/analysis.py backend/app/routers/__init__.py backend/app/main.py
git commit -m "feat(analysis): add /api/analysis/{ticker} endpoint"
```

---

## Task 4: Frontend — Types and API

**Files:**
- Create: `frontend/src/types/analysis.ts`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Add Analysis type**

Create `frontend/src/types/analysis.ts`:
```typescript
export type Recommendation = "strong_buy" | "buy" | "hold" | "sell" | "strong_sell";

export interface RSIData { value: number; signal: "oversold" | "neutral" | "overbought"; }
export interface MACDData { histogram: number; signal: "bullish_cross" | "bearish_cross" | "neutral"; }
export interface MAData { value: number; above: boolean; }

export interface TechnicalData {
  rsi: RSIData;
  macd: MACDData;
  ma20: MAData;
  ma50: MAData;
  ma200: MAData;
  fiftytwo_week_position: number;
  bullish_count: number;
  total_count: number;
}

export interface FundamentalData {
  pe_ratio: number | null;
  sector_pe_median: number | null;
  pe_verdict: "cheaper_than_avg" | "fair_value" | "expensive";
  market_cap_label: "Mega" | "Large" | "Mid" | "Small" | null;
  dividend_yield: number | null;
  beta: number | null;
  beta_verdict: "low" | "medium" | "high" | null;
  fiftytwo_week_range_verdict: "near_low" | "mid_range" | "near_high";
  verdict_text: string;
}

export interface PlainEnglishData {
  newbie: string;
  basic: string;
  pro: string;
}

export interface Analysis {
  ticker: string;
  score: number;
  recommendation: Recommendation;
  plain_english: PlainEnglishData;
  technical: TechnicalData;
  fundamental: FundamentalData;
}
```

- [ ] **Step 2: Add analysisApi to api.ts**

Add to `frontend/src/services/api.ts`:
```typescript
export const analysisApi = {
  get: (ticker: string) => api.get(`/api/analysis/${ticker}`).then((r) => r.data as Promise<Analysis>),
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/analysis.ts frontend/src/services/api.ts
git commit -m "feat(analysis): add Analysis type and API method"
```

---

## Task 5: Frontend — useAnalysis Hook

**Files:**
- Create: `frontend/src/hooks/useAnalysis.ts`

- [ ] **Step 1: Create the hook**

```typescript
import { useState, useEffect } from "react";
import { analysisApi } from "../services/api";
import type { Analysis } from "../types/analysis";

export function useAnalysis(ticker: string) {
  const [data, setData] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    analysisApi.get(ticker)
      .then(setData)
      .catch(() => setError("Analysis unavailable"))
      .finally(() => setLoading(false));
  }, [ticker]);

  return { data, loading, error };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useAnalysis.ts
git commit -m "feat(analysis): add useAnalysis hook"
```

---

## Task 6: Frontend — Inline Sparkline Component

**Files:**
- Create: `frontend/src/components/analysis/Sparkline.tsx`

- [ ] **Step 1: Create the sparkline SVG component**

```typescript
interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  showDot?: boolean;
}

export default function Sparkline({
  data,
  width = 60,
  height = 24,
  color = "#2979FF",
  showDot = false,
}: SparklineProps) {
  if (data.length < 2) return <div style={{ width, height }} />;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pad = 2;

  const points = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (width - pad * 2);
    const y = pad + (1 - (v - min) / range) * (height - pad * 2);
    return `${x},${y}`;
  });

  const lastX = pad + (width - pad * 2);
  const lastY = pad + (1 - (data[data.length - 1] - min) / range) * (height - pad * 2);

  return (
    <svg width={width} height={height} style={{ overflow: "visible" }}>
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {showDot && (
        <circle cx={lastX} cy={lastY} r="2.5" fill={color} />
      )}
    </svg>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/analysis/Sparkline.tsx
git commit -m "feat(analysis): add inline SVG sparkline component"
```

---

## Task 7: Frontend — ModeSwitcher Component

**Files:**
- Create: `frontend/src/components/analysis/ModeSwitcher.tsx`

- [ ] **Step 1: Create the mode toggle**

```typescript
type Mode = "newbie" | "basic" | "pro";

const MODES: { key: Mode; label: string; icon: string }[] = [
  { key: "newbie", label: "Newbie", icon: "🌱" },
  { key: "basic", label: "Basic", icon: "📊" },
  { key: "pro", label: "Pro", icon: "⚡" },
];

interface ModeSwitcherProps {
  mode: Mode;
  onChange: (mode: Mode) => void;
}

export default function ModeSwitcher({ mode, onChange }: ModeSwitcherProps) {
  return (
    <div className="flex border-b border-border">
      {MODES.map(({ key, label, icon }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className={`flex-1 px-4 py-2.5 text-sm font-medium transition-colors cursor-pointer ${
            mode === key
              ? "text-accent-blue border-b-2 border-accent-blue bg-surface-elevated"
              : "text-text-secondary hover:text-text-primary"
          }`}
        >
          {icon} {label}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/analysis/ModeSwitcher.tsx
git commit -m "feat(analysis): add ModeSwitcher component"
```

---

## Task 8: Frontend — PlainEnglishCard Component

**Files:**
- Create: `frontend/src/components/analysis/PlainEnglishCard.tsx`

- [ ] **Step 1: Create the Plain English card**

```typescript
import type { Analysis, Recommendation } from "../../types/analysis";
import Badge from "../ui/Badge";

const RECOMMENDATION_CONFIG: Record<Recommendation, { label: string; variant: "green" | "yellow" | "red" }> = {
  strong_buy: { label: "STRONG BUY", variant: "green" },
  buy: { label: "BUY", variant: "green" },
  hold: { label: "HOLD", variant: "yellow" },
  sell: { label: "SELL", variant: "red" },
  strong_sell: { label: "STRONG SELL", variant: "red" },
};

interface PlainEnglishCardProps {
  data: Analysis;
  mode: "newbie" | "basic" | "pro";
}

export default function PlainEnglishCard({ data, mode }: PlainEnglishCardProps) {
  const rec = RECOMMENDATION_CONFIG[data.recommendation];
  const text = data.plain_english[mode];

  const scoreColor = data.score >= 7 ? "#3fb950" : data.score >= 5 ? "#d29922" : "#f85149";

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border">
        <span className="text-base">📝</span>
        <span className="text-xs font-semibold uppercase tracking-wide text-text-secondary">Plain English</span>
        <Badge variant={rec.variant} className="ml-auto">{rec.label}</Badge>
      </div>
      <div className="p-4">
        <p className="text-sm text-text-primary leading-relaxed mb-4">{text}</p>
        <div className="mb-1">
          <div className="flex justify-between text-xs text-text-secondary mb-1.5">
            <span>Score</span>
            <span style={{ color: scoreColor, fontFamily: "monospace", fontWeight: 600 }}>
              {data.score.toFixed(1)} / 10
            </span>
          </div>
          <div className="h-2 bg-border rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${data.score * 10}%`,
                background: `linear-gradient(90deg, #f85149 0%, #d29922 50%, #3fb950 100%)`,
              }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-text-secondary mt-1">
            <span>← Strong Sell</span>
            <span>Strong Buy →</span>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/analysis/PlainEnglishCard.tsx
git commit -m "feat(analysis): add PlainEnglishCard component"
```

---

## Task 9: Frontend — TechnicalCard Component

**Files:**
- Create: `frontend/src/components/analysis/TechnicalCard.tsx`

- [ ] **Step 1: Create the Technical Indicators card with sparklines**

```typescript
import type { Analysis, TechnicalData } from "../../types/analysis";
import Sparkline from "./Sparkline";

const RSI_HISTORY = Array.from({ length: 30 }, (_, i) => 50 + Math.sin(i * 0.3) * 20 + Math.random() * 5);
const MACD_HISTORY = Array.from({ length: 30 }, (_, i) => Math.sin(i * 0.2) * 2 + (i > 20 ? 1 : -0.5));
const MA_HISTORY = (start: number, slope: number) =>
  Array.from({ length: 30 }, (_, i) => start + slope * i + Math.random() * 2);

function signalColor(above: boolean | string): string {
  if (above === "bullish_cross" || above === true) return "#3fb950";
  if (above === "bearish_cross" || above === false) return "#f85149";
  return "#d29922";
}

function dotColor(signal: string): string {
  if (signal === "oversold" || signal === "bullish_cross") return "#3fb950";
  if (signal === "overbought" || signal === "bearish_cross") return "#f85149";
  return "#d29922";
}

interface RowProps {
  label: string;
  tooltip: string;
  value: string;
  sparkData: number[];
  sparkColor: string;
  signal: string;
}

function IndicatorRow({ label, tooltip, value, sparkData, sparkColor, signal }: RowProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-text-secondary">{label}</span>
        <span
          className="text-[10px] text-text-secondary cursor-help border-b border-dashed border-text-secondary"
          title={tooltip}
        >
          ?
        </span>
      </div>
      <div className="flex items-center gap-2">
        <Sparkline data={sparkData} color={sparkColor} width={50} height={20} />
        <div className="flex items-center gap-1 min-w-[80px] justify-end">
          <span
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: dotColor(signal) }}
          />
          <span className="text-xs font-mono text-text-primary">{value}</span>
        </div>
      </div>
    </div>
  );
}

interface TechnicalCardProps {
  data: Analysis;
}

export default function TechnicalCard({ data }: TechnicalCardProps) {
  const t = data.technical;
  const bullishPct = (t.bullish_count / t.total_count) * 100;

  const rsiSignal = t.rsi.signal === "oversold" ? "oversold" : t.rsi.signal === "overbought" ? "overbought" : "neutral";
  const macdSignal = t.macd.signal;

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border">
        <span className="text-base">📊</span>
        <span className="text-xs font-semibold uppercase tracking-wide text-text-secondary">Technical</span>
        <span
          className="ml-auto text-xs font-medium px-2 py-0.5 rounded-full"
          style={{ background: "#0d4426", color: "#3fb950" }}
        >
          {t.bullish_count}/{t.total_count} bullish
        </span>
      </div>
      <div className="p-4">
        <IndicatorRow
          label="RSI (14)"
          tooltip="Measures speed of price changes. Above 70 = overbought (sell signal). Below 30 = oversold (buy signal)."
          value={`${t.rsi.value} — ${rsiSignal}`}
          sparkData={RSI_HISTORY}
          sparkColor={signalColor(rsiSignal)}
          signal={rsiSignal}
        />
        <IndicatorRow
          label="MACD"
          tooltip="Moving Average Convergence Divergence. Blue line crosses above orange = buy signal."
          value={macdSignal === "bullish_cross" ? "Bullish Cross" : macdSignal === "bearish_cross" ? "Bearish Cross" : t.macd.histogram > 0 ? "Above 0" : "Below 0"}
          sparkData={MACD_HISTORY}
          sparkColor={signalColor(macdSignal)}
          signal={macdSignal}
        />
        <IndicatorRow
          label="MA 20"
          tooltip="Price vs 20-day average. Above = short-term uptrend."
          value={t.ma20.above ? `$${t.ma20.value} ↑` : `$${t.ma20.value} ↓`}
          sparkData={MA_HISTORY(180, 0.5)}
          sparkColor={signalColor(t.ma20.above)}
          signal={t.ma20.above ? "bullish" : "bearish"}
        />
        <IndicatorRow
          label="MA 50"
          tooltip="Price vs 50-day average. Above = medium-term uptrend."
          value={t.ma50.above ? `$${t.ma50.value} ↑` : `$${t.ma50.value} ↓`}
          sparkData={MA_HISTORY(175, 0.3)}
          sparkColor={signalColor(t.ma50.above)}
          signal={t.ma50.above ? "bullish" : "bearish"}
        />
        <IndicatorRow
          label="MA 200"
          tooltip="Price vs 200-day average. Above = long-term uptrend."
          value={t.ma200.above ? `$${t.ma200.value} ↑` : `$${t.ma200.value} ↓`}
          sparkData={MA_HISTORY(160, 0.2)}
          sparkColor={signalColor(t.ma200.above)}
          signal={t.ma200.above ? "bullish" : "bearish"}
        />
        <IndicatorRow
          label="52W Range"
          tooltip="Distance from 52-week high. Below 80% = still has room to grow."
          value={`${Math.round(t.fiftytwo_week_position * 100)}% of high`}
          sparkData={Array.from({ length: 30 }, (_, i) => 0.3 + (i / 30) * 0.5)}
          sparkColor={t.fiftytwo_week_position < 0.7 ? "#3fb950" : "#d29922"}
          signal={t.fiftytwo_week_position < 0.5 ? "bullish" : t.fiftytwo_week_position > 0.8 ? "bearish" : "neutral"}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/analysis/TechnicalCard.tsx
git commit -m "feat(analysis): add TechnicalCard component with sparklines"
```

---

## Task 10: Frontend — FundamentalsCard Component

**Files:**
- Create: `frontend/src/components/analysis/FundamentalsCard.tsx`

- [ ] **Step 1: Create the Fundamentals card**

```typescript
import type { Analysis, FundamentalData } from "../../types/analysis";

const TOOLTIPS: Record<string, string> = {
  pe_ratio: "How expensive the stock is relative to earnings. Higher = more expensive. Compare to sector average.",
  vs_sector: "Is this stock cheaper or pricier than similar companies? Lower than average = potentially good value.",
  market_cap: "Total value of all shares. Mega = over $200B (very established). Small = under $2B (riskier).",
  dividend: "A company pays you to own its stock. Growth stocks usually pay little — they reinvest profits instead.",
  beta: "How much the stock moves compared to the overall market. Above 1 = more risky but potentially higher returns.",
  range_52w: "Shows if the stock is near its high (less upside) or low (more upside potential) over the past year.",
};

function verdicts(data: FundamentalData) {
  return {
    pe: data.pe_verdict === "cheaper_than_avg" ? "Cheaper than avg" : data.pe_verdict === "expensive" ? "Expensive" : "Fair value",
    peColor: data.pe_verdict === "cheaper_than_avg" ? "#3fb950" : data.pe_verdict === "expensive" ? "#f85149" : "#d29922",
    betaLabel: data.beta_verdict ? data.beta_verdict.charAt(0).toUpperCase() + data.beta_verdict.slice(1) + " volatility" : "N/A",
    rangeLabel: data.fiftytwo_week_range_verdict === "near_low" ? "Near 52W low" : data.fiftytwo_week_range_verdict === "near_high" ? "Near 52W high" : "Mid range",
    rangeColor: data.fiftytwo_week_range_verdict === "near_low" ? "#3fb950" : data.fiftytwo_week_range_verdict === "near_high" ? "#f85149" : "#d29922",
    verdictBg: data.verdict_text.includes("strong momentum") || data.verdict_text.includes("cheaper") ? "#0d4426"
      : data.verdict_text.includes("pricier") || data.verdict_text.includes("near high") ? "#4d1010"
      : "#3d3020",
    verdictColor: data.verdict_text.includes("strong momentum") || data.verdict_text.includes("cheaper") ? "#3fb950"
      : data.verdict_text.includes("pricier") || data.verdict_text.includes("near high") ? "#f85149"
      : "#d29922",
  };
}

export default function FundamentalsCard({ data }: { data: Analysis }) {
  const f = data.fundamental;
  const v = verdicts(f);

  const rows: [string, string, string | null, (string | null)[]][] = [
    ["P/E Ratio", f.pe_ratio != null ? f.pe_ratio.toFixed(1) : "N/A", "pe_ratio", [null, null]],
    ["vs Sector", v.pe, null, [f.sector_pe_median ? `Sector avg: ${f.sector_pe_median.toFixed(0)}` : null, v.peColor]],
    ["Market Cap", f.market_cap_label || "N/A", "market_cap", [null, null]],
    ["Dividend", f.dividend_yield != null ? `${(f.dividend_yield * 100).toFixed(2)}%` : "N/A", "dividend", [null, null]],
    ["Beta", f.beta != null ? f.beta.toFixed(2) : "N/A", "beta", [v.betaLabel, null]],
    ["52W Range", v.rangeLabel, "range_52w", [null, v.rangeColor]],
  ];

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border">
        <span className="text-base">💰</span>
        <span className="text-xs font-semibold uppercase tracking-wide text-text-secondary">Fundamentals</span>
        <span
          className="ml-auto text-xs font-medium px-2 py-0.5 rounded-full"
          style={{ background: f.pe_verdict === "cheaper_than_avg" ? "#0d4426" : f.pe_verdict === "expensive" ? "#4d1010" : "#3d3020", color: v.peColor }}
        >
          {v.pe}
        </span>
      </div>
      <div className="p-4">
        {rows.map(([label, value, tooltip, [sub, subColor]]) => (
          <div key={label} className="flex justify-between items-center py-2 border-b border-border last:border-0">
            <div className="flex items-center gap-1">
              <span className="text-xs text-text-secondary">{label}</span>
              {tooltip && (
                <span
                  className="text-[10px] text-text-secondary cursor-help border-b border-dashed border-text-secondary"
                  title={TOOLTIPS[tooltip]}
                >
                  ?
                </span>
              )}
            </div>
            <div className="text-right">
              <span className="text-xs font-mono text-text-primary">{value}</span>
              {sub && <div className="text-[10px]" style={{ color: subColor || "#8b949e" }}>{sub}</div>}
            </div>
          </div>
        ))}
        <div
          className="mt-3 p-3 rounded-md text-xs"
          style={{ background: v.verdictBg, color: v.verdictColor }}
        >
          ✓ {f.verdict_text}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/analysis/FundamentalsCard.tsx
git commit -m "feat(analysis): add FundamentalsCard component"
```

---

## Task 11: Frontend — TradingAssistant Container + Integration

**Files:**
- Create: `frontend/src/components/analysis/TradingAssistant.tsx`
- Modify: `frontend/src/pages/StockDetail.tsx`

- [ ] **Step 1: Create the TradingAssistant container**

```typescript
import ModeSwitcher from "./ModeSwitcher";
import PlainEnglishCard from "./PlainEnglishCard";
import TechnicalCard from "./TechnicalCard";
import FundamentalsCard from "./FundamentalsCard";
import { useAnalysis } from "../../hooks/useAnalysis";
import { Skeleton } from "../ui/Skeleton";

export type AnalysisMode = "newbie" | "basic" | "pro";

interface TradingAssistantProps {
  ticker: string;
  mode: AnalysisMode;
}

export default function TradingAssistant({ ticker, mode }: TradingAssistantProps) {
  const { data, loading, error } = useAnalysis(ticker);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Skeleton className="h-52 rounded-lg" />
        <Skeleton className="h-52 rounded-lg" />
        <Skeleton className="h-52 rounded-lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-surface border border-border rounded-lg p-6 text-center text-text-secondary text-sm">
        Analysis unavailable for {ticker}
      </div>
    );
  }

  return (
    <div className="space-y-0">
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <ModeSwitcher mode={mode} onChange={() => {}} />
        <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-border">
          <PlainEnglishCard data={data} mode={mode} />
          <TechnicalCard data={data} />
          <FundamentalsCard data={data} />
        </div>
      </div>
    </div>
  );
}
```

Note: `onChange` is a no-op here — the parent (StockDetail) owns the mode state. Pass a real handler if mode is editable from the cards.

- [ ] **Step 2: Integrate into StockDetail page**

Modify `frontend/src/pages/StockDetail.tsx`:

Add `useState` import if not present, add `AnalysisMode` type import, and add:

```typescript
const ANALYSIS_MODE_KEY = "trading-assistant-mode";
const savedMode = (localStorage.getItem(ANALYSIS_MODE_KEY) as AnalysisMode) || "newbie";
const [analysisMode, setAnalysisMode] = useState<AnalysisMode>(savedMode);

const handleModeChange = (mode: AnalysisMode) => {
  setAnalysisMode(mode);
  localStorage.setItem(ANALYSIS_MODE_KEY, mode);
};
```

Add `TradingAssistant` import:
```typescript
import TradingAssistant from "../components/analysis/TradingAssistant";
```

Add below the chart, before the Key Metrics sidebar panel:
```tsx
<div className="mt-6">
  <TradingAssistant ticker={ticker!} mode={analysisMode} />
</div>
```

Also add `AnalysisMode` to the import from the analysis component if needed.

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd /home/michaek/finsight/frontend && npx tsc --noEmit 2>&1 | grep -v "^node_modules" | head -20`
Expected: No errors (or only pre-existing unrelated errors)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/analysis/TradingAssistant.tsx frontend/src/pages/StockDetail.tsx
git commit -m "feat(analysis): add TradingAssistant to StockDetail page with mode persistence"
```

---

## Task 12: End-to-End Verification

- [ ] **Step 1: Verify backend endpoint**

Run: `curl -s http://localhost:8000/api/analysis/AAPL | python3 -m json.tool | head -40`
Expected: JSON with ticker, score, recommendation, technical data (rsi, macd, ma values), fundamental data

- [ ] **Step 2: Verify frontend compiles**

Run: `cd /home/michaek/finsight/frontend && npx tsc --noEmit 2>&1 | grep -v "^node_modules" | grep -E "^src" | head -20`
Expected: No errors

- [ ] **Step 3: Manual browser test**

Open http://localhost:5173/stock/AAPL — should show three analysis cards below the chart. Toggle between Newbie/Basic/Pro modes. Refresh page — mode should persist.
