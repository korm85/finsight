import { useState, useEffect, useCallback } from "react";
import PageHeader from "../components/layout/PageHeader";
import MarketOverview from "../components/market/MarketOverview";
import TopMovers from "../components/market/TopMovers";
import WatchlistPanel from "../components/watchlist/WatchlistPanel";
import PortfolioSummary from "../components/portfolio/PortfolioSummary";
import { useAutoRefresh } from "../hooks/useAutoRefresh";
import { portfolioApi, watchlistApi } from "../services/api";
import type { Portfolio, Watchlist } from "../types";

const REFRESH_INTERVAL = 60_000; // 60 seconds

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);

  const fetchAll = useCallback(() => {
    portfolioApi.get().then(setPortfolio).catch(console.error);
    watchlistApi.getAll().then(setWatchlists).catch(console.error);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);
  useAutoRefresh(fetchAll, REFRESH_INTERVAL);

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Your financial overview" />
      <div className="space-y-6">
        <MarketOverview />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {portfolio && <PortfolioSummary portfolio={portfolio} />}
          <TopMovers />
        </div>
        <WatchlistPanel watchlists={watchlists} />
      </div>
    </div>
  );
}
