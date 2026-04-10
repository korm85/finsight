import { useState, useEffect } from "react";
import { marketApi } from "../services/api";
import type { IndexQuote, TopMover } from "../types";

const REFRESH_INTERVAL = 60_000; // 60 seconds — single fetch shared by all subscribers

interface MarketState {
  indices: IndexQuote[];
  gainers: TopMover[];
  losers: TopMover[];
  mostActive: TopMover[];
  loading: boolean;
  lastUpdated: number | null;
}

const initialState: MarketState = {
  indices: [],
  gainers: [],
  losers: [],
  mostActive: [],
  loading: true,
  lastUpdated: null,
};

// Module-level singleton state
let marketState: MarketState = { ...initialState };
let subscribers = new Set<(state: MarketState) => void>();
let refreshTimer: ReturnType<typeof setTimeout> | null = null;

async function fetchAndBroadcast() {
  marketState = { ...marketState, loading: true };
  broadcast();

  try {
    const data = await marketApi.overview();
    marketState = {
      indices: data.indices || [],
      gainers: data.top_movers?.gainers || [],
      losers: data.top_movers?.losers || [],
      mostActive: data.top_movers?.most_active || [],
      loading: false,
      lastUpdated: Date.now(),
    };
  } catch {
    marketState = { ...marketState, loading: false };
  }
  broadcast();

  // Schedule next refresh
  if (refreshTimer) clearTimeout(refreshTimer);
  refreshTimer = setTimeout(fetchAndBroadcast, REFRESH_INTERVAL);
}

function broadcast() {
  for (const sub of subscribers) {
    sub({ ...marketState });
  }
}

export function useMarketData() {
  const [state, setState] = useState<MarketState>({ ...marketState });

  useEffect(() => {
    subscribers.add(setState);
    // Emit current state immediately on subscribe
    setState({ ...marketState });
    // Start fetching if not already started
    if (refreshTimer === null) {
      fetchAndBroadcast();
    }
    return () => {
      subscribers.delete(setState);
    };
  }, []);

  return {
    ...state,
    refresh: fetchAndBroadcast,
  };
}
