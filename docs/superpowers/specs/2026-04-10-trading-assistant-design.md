# Trading Assistant — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan.

**Goal:** Add a trading assistant panel to the Stock Detail page that helps users (especially newbies) understand when to buy or sell a stock through plain-English analysis, real computed technical indicators, and contextualized fundamental metrics — all with a mode switcher (Newbie / Basic / Pro).

**Architecture:** A new backend endpoint `/api/analysis/{ticker}` computes RSI, MACD, MAs, and generates a plain-English summary + score. A new frontend `TradingAssistant` component renders three cards on the Stock Detail page. A mode preference is stored in `localStorage` and passed to the component as a prop that determines content depth.

**Tech Stack:** React + TypeScript (frontend), FastAPI + Python (backend), yfinance for price history (already in use).

---

## 1. Mode Switcher

**Location:** Top of the Trading Assistant panel on Stock Detail page, above the three cards.

**Three modes:**
- 🌱 **Newbie** — Full explanations, every term defined, simple language
- 📊 **Basic** — Intermediate explanations, assumes some familiarity
- ⚡ **Pro** — Concise, technical, includes position sizing hints

**Persistence:** Saved to `localStorage` under key `trading-assistant-mode`. Defaults to `newbie` on first visit.

**UI:** Three equal-width toggle buttons. Active mode is highlighted with accent-blue underline + background.

---

## 2. Backend: `GET /api/analysis/{ticker}`

**Response shape:**

```json
{
  "ticker": "NVDA",
  "score": 7.5,
  "recommendation": "buy",
  "plain_english": {
    "newbie": "NVDA is up 2.5% today and trading above its average price over the last 50 days...",
    "basic": "NVDA is showing bullish momentum with price above both 20-day and 50-day moving averages...",
    "pro": "MACD histogram expanding at +2.3, price rejecting at $190 resistance..."
  },
  "technical": {
    "rsi": { "value": 45.3, "signal": "neutral" },
    "macd": { "histogram": 2.3, "signal": "bullish_cross" },
    "ma20": { "value": 185.2, "above": true },
    "ma50": { "value": 178.4, "above": true },
    "ma200": { "value": 152.1, "above": true },
    "fiftytwo_week_position": 0.72,
    "bullish_count": 4,
    "total_count": 6
  },
  "fundamental": {
    "pe_ratio": 28.5,
    "sector_pe_median": 30.0,
    "pe_verdict": "cheaper_than_avg",
    "market_cap_label": "Mega",
    "dividend_yield": 0.0002,
    "beta": 1.71,
    "beta_verdict": "high",
    "fiftytwo_week_range_verdict": "near_high",
    "verdict_text": "Fair valuation vs peers, strong momentum, but near 52W high — wait for dip"
  }
}
```

**Computing RSI (14-day):**
1. Fetch 6 months of daily close prices via yfinance
2. Calculate 14-day gains and losses
3. Average gain / (average gain + average loss) = RS → RSI = 100 - (100 / (1 + RS))

**Computing MACD (12/26/9):**
1. EMA-12 of close prices
2. EMA-26 of close prices
3. MACD line = EMA-12 - EMA-26
4. Signal line = 9-period EMA of MACD line
5. Histogram = MACD line - Signal line

**Computing Moving Averages:**
- MA20: Simple 20-day average of close prices
- MA50: Simple 50-day average
- MA200: Simple 200-day average (fetch 12 months for this)

**Plain English generation (rules-based):**
- Derive from: price vs MAs, RSI level, MACD signal, 52W position, P/E vs sector, trend direction
- Score: weighted sum of bullish signals (RSI<70=good, price>MA20=good, MACD bullish=good, P/E<sector=good, near_52w_low=good, beta<1.5=good) normalized to 0-10
- Recommendation: score >= 7 = "strong_buy", >= 5.5 = "buy", >= 4.5 = "hold", >= 3 = "sell", else "strong_sell"

**Sector P/E median:** Hardcoded map of sector names to median P/E (Technology: 30, Healthcare: 20, Financial: 12, Consumer: 25, Energy: 10, Industrial: 22, Utilities: 18). Sector derived from Yahoo Finance `sector` field on the quote.

---

## 3. Frontend: `TradingAssistant` Component

**File:** `src/components/analysis/TradingAssistant.tsx`

**Props:**
```typescript
interface TradingAssistantProps {
  ticker: string;
  mode: "newbie" | "basic" | "pro";
}
```

**Layout:** Horizontal row of three cards (grid-cols-3 on desktop, stack on mobile), each card has a header with icon + title + badge, and a body.

**Mode toggle:** Rendered inside the component's parent (StockDetail page), passes mode as prop.

**API call:** Uses a new `analysisApi.get(ticker)` call that hits `GET /api/analysis/{ticker}`. Result cached in React state (not singleton — each stock has its own analysis).

---

## 4. Card: Plain English Summary (left)

**Header badge:** Score + recommendation text (green BUY / yellow HOLD / red SELL).

**Score bar:** 0-10 gradient bar. Tick marks for each section:
`← Strong Sell | Sell | Hold | Buy | Strong Buy →`

**Content per mode:**
- `newbie`: Full sentences, no jargon, explicit mention of what each signal means for the user's decision
- `basic`: Concise summary, some technical terms used but explained in one phrase
- `pro`: Data-dense, includes RSI/MACD values, position sizing hint

---

## 5. Card: Technical Indicators (center)

**Layout:** 6 rows, each with indicator name + sparkline + value + signal dot.

**Sparklines:** Use a lightweight inline SVG sparkline (no external lib). Draw a polyline of the last 30 daily RSI/MACD/price values. SVG rendered inline in JSX — no recharts dependency needed.

**Signal dot colors:**
- Green (`dot-green`): Bullish signal
- Yellow (`dot-yellow`): Neutral
- Red (`dot-red`): Bearish signal

**Row definitions:**
1. **RSI (14)** — sparkline of RSI values, dot color based on: <30=green, >70=red, else=yellow
2. **MACD** — sparkline of MACD histogram, dot color based on: histogram>0=green, <0=red
3. **MA 20** — sparkline of price vs MA20 ratio, dot: price above=green else=red
4. **MA 50** — same pattern
5. **MA 200** — same pattern
6. **52W Range** — percentage bar showing current price position in 52W range, dot: <50%=green, >80%=red, else=yellow

**Summary line:** "4 of 6 indicators bullish" in green, or appropriate color.

---

## 6. Card: Fundamentals (right)

**Layout:** 6 metric rows + a verdict box at the bottom.

**Metric rows:** Each has a label (with `?` tooltip) and a value with contextual color.

**Verdict box:** Background color-coded (green/yellow/red) with the combined verdict text.

**Tooltip definitions (shown on hover):**
| Metric | Newbie tooltip |
|--------|---------------|
| P/E Ratio | "How expensive the stock is relative to its earnings. Higher = more expensive. Compare to sector average." |
| vs Sector | "Is this stock cheaper or pricier than similar companies? Lower than average = potentially good value." |
| Market Cap | "Total value of all shares. Mega = over $200B (very established). Small = under $2B (riskier)." |
| Dividend | "A company pays you to own its stock. Growth stocks like NVDA usually pay little — they reinvest profits instead." |
| Beta | "How much the stock moves compared to the overall market. Above 1 = more risky but potentially higher returns." |
| 52W Range | "Shows if the stock is near its high (less upside) or low (more upside potential) over the past year." |

---

## 7. Integration: StockDetail Page

**Layout change:** Below the chart row, add the `TradingAssistant` component before the Key Metrics sidebar panel.

```tsx
{/* New — Trading Assistant */}
<div className="mt-6">
  <TradingAssistantPanel ticker={ticker!} mode={analysisMode} />
</div>
```

**Mode state:** Managed in `StockDetail.tsx` via `useState<"newbie" | "basic" | "pro">`, initialized from `localStorage`.

---

## 8. Files to Create/Modify

### New files
- `backend/app/routers/analysis.py` — new FastAPI router
- `backend/app/services/analysis_service.py` — RSI, MACD, MA computation + summary generation
- `backend/app/schemas/analysis.py` — Pydantic request/response schemas
- `frontend/src/components/analysis/TradingAssistant.tsx` — main component
- `frontend/src/components/analysis/TechnicalCard.tsx` — technical indicators card with sparklines
- `frontend/src/components/analysis/FundamentalsCard.tsx` — fundamentals card
- `frontend/src/components/analysis/PlainEnglishCard.tsx` — plain English summary card
- `frontend/src/components/analysis/ModeSwitcher.tsx` — toggle UI
- `frontend/src/hooks/useAnalysis.ts` — fetches and caches analysis data
- `frontend/src/services/api.ts` — add `analysisApi.get(ticker)`
- `frontend/src/types/index.ts` — add `Analysis` type

### Modify files
- `frontend/src/pages/StockDetail.tsx` — add TradingAssistant component, mode state, localStorage
- `frontend/src/components/layout/Sidebar.tsx` — (no change needed, analysis is per-stock not global)
