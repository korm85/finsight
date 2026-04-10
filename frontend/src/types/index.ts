export interface TopMover {
  ticker: string;
  name: string;
  price: number;
  change_pct: number;
  volume: number;
}

export interface IndexQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  sparkline: number[];
}

export interface Quote {
  ticker: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  high: number;
  low: number;
  open: number;
  previous_close: number;
  volume: number;
  market_cap?: number;
  pe_ratio?: number;
  week_52_high?: number;
  week_52_low?: number;
  dividend_yield?: number;
  beta?: number;
}

export interface ChartCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartData {
  ticker: string;
  candles: ChartCandle[];
  indicators: Record<string, number[]>;
}

export interface Holding {
  id: number;
  ticker: string;
  name: string;
  quantity: number;
  avg_cost: number;
  purchase_date?: string;
  current_price?: number;
  market_value?: number;
  pnl?: number;
  pnl_pct?: number;
  created_at: string;
}

export interface Portfolio {
  holdings: Holding[];
  total_value: number;
  total_cost: number;
  total_pnl: number;
  total_pnl_pct: number;
  day_pnl: number;
}

export interface Watchlist {
  id: number;
  name: string;
  items: WatchlistItem[];
  created_at: string;
}

export interface WatchlistItem {
  ticker: string;
  name: string;
  price: number;
  change_pct: number;
}

export type AlertCondition =
  | "price_above"
  | "price_below"
  | "price_crosses"
  | "pct_change_above"
  | "pct_change_below"
  | "volume_above"
  | "earnings_within";

export type AlertStatus = "active" | "paused" | "triggered";

export interface Alert {
  id: number;
  ticker: string;
  condition: AlertCondition;
  threshold: number;
  channel_inapp: boolean;
  channel_email: boolean;
  channel_push: boolean;
  status: AlertStatus;
  last_triggered_at?: string;
  created_at: string;
}

export interface AlertHistory {
  id: number;
  alert_id: number;
  ticker: string;
  condition: AlertCondition;
  threshold: number;
  triggered_at: string;
  delivered_inapp: boolean;
  delivered_email: boolean;
  delivered_push: boolean;
}

export interface SearchResult {
  ticker: string;
  name: string;
  exchange: string;
  type: string;
}

export interface NewsItem {
  title: string;
  link: string;
  pubDate: string;
  source: string;
}