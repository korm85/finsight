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
