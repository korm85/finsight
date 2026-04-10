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