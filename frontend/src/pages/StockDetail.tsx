import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import PageHeader from "../components/layout/PageHeader";
import PriceChart from "../components/chart/PriceChart";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import TradingAssistant from "../components/analysis/TradingAssistant";
import type { AnalysisMode } from "../components/analysis/TradingAssistant";
import { useAutoRefresh } from "../hooks/useAutoRefresh";
import { marketApi, portfolioApi } from "../services/api";
import type { Quote } from "../types";

const REFRESH_INTERVAL = 10_000; // 10 seconds

export default function StockDetail() {
  const { ticker } = useParams<{ ticker: string }>();
  const navigate = useNavigate();
  const [quote, setQuote] = useState<Quote | null>(null);
  const [loading, setLoading] = useState(true);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [qty, setQty] = useState("");
  const [price, setPrice] = useState("");

  const ANALYSIS_MODE_KEY = "trading-assistant-mode";
  const VALID_MODES: AnalysisMode[] = ["newbie", "basic", "pro"];
  const savedMode = VALID_MODES.includes(localStorage.getItem(ANALYSIS_MODE_KEY) as AnalysisMode)
    ? (localStorage.getItem(ANALYSIS_MODE_KEY) as AnalysisMode)
    : "newbie";
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>(savedMode);

  const handleModeChange = (mode: AnalysisMode) => {
    setAnalysisMode(mode);
    localStorage.setItem(ANALYSIS_MODE_KEY, mode);
  };

  if (!ticker) {
    return <div className="text-text-secondary p-8">No ticker specified</div>;
  }

  const fetchQuote = useCallback(() => {
    marketApi.quote(ticker)
      .then(setQuote)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [ticker]);

  useEffect(() => { fetchQuote(); }, [fetchQuote]);
  useAutoRefresh(fetchQuote, REFRESH_INTERVAL);

  const isPositive = (quote?.change_pct ?? 0) >= 0;

  if (loading) return <div className="text-text-secondary">Loading...</div>;
  if (!quote) return <div className="text-text-secondary">Ticker not found</div>;

  return (
    <div>
      <PageHeader
        title={ticker || ""}
        subtitle={quote.name}
        action={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => navigate("/watchlist")}>+ Watchlist</Button>
            <Button onClick={() => setAddModalOpen(true)}>+ Portfolio</Button>
          </div>
        }
      />
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <div className="bg-surface border border-border rounded-lg p-4">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl font-bold font-mono">${quote.price.toFixed(2)}</span>
              <Badge variant={isPositive ? "green" : "red"}>
                {isPositive ? "+" : ""}{quote.change_pct.toFixed(2)}%
              </Badge>
              <span className={`text-sm font-mono ${isPositive ? "text-accent-green" : "text-accent-red"}`}>
                {isPositive ? "+" : ""}${quote.change.toFixed(2)}
              </span>
            </div>
            <PriceChart ticker={ticker} />
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-surface border border-border rounded-lg p-4">
            <div className="text-xs text-text-secondary uppercase tracking-wide mb-3">Key Metrics</div>
            <div className="space-y-2.5">
              {[
                ["Market Cap", quote.market_cap ? `$${(quote.market_cap / 1e9).toFixed(2)}B` : "N/A"],
                ["P/E Ratio", quote.pe_ratio?.toFixed(2) || "N/A"],
                ["52W High", quote.week_52_high ? `$${quote.week_52_high.toFixed(2)}` : "N/A"],
                ["52W Low", quote.week_52_low ? `$${quote.week_52_low.toFixed(2)}` : "N/A"],
                ["Dividend", quote.dividend_yield ? `${(quote.dividend_yield * 100).toFixed(2)}%` : "N/A"],
                ["Beta", quote.beta?.toFixed(2) || "N/A"],
                ["Volume", quote.volume?.toLocaleString() || "N/A"],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between text-sm">
                  <span className="text-text-secondary">{label}</span>
                  <span className="font-mono text-text-primary">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <TradingAssistant ticker={ticker} mode={analysisMode} onModeChange={handleModeChange} />
      </div>

      <Modal open={addModalOpen} onClose={() => setAddModalOpen(false)} title={`Add ${ticker} to Portfolio`}>
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-text-secondary mb-1">Quantity</label>
            <input
              type="number"
              value={qty}
              onChange={(e) => setQty(e.target.value)}
              className="w-full bg-surface border border-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-blue"
              placeholder="e.g. 10"
            />
          </div>
          <div>
            <label className="block text-xs text-text-secondary mb-1">Average Cost ($)</label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full bg-surface border border-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-blue"
              placeholder={quote.price.toFixed(2)}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setAddModalOpen(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (!qty || !price) return;
                portfolioApi.addHolding({
                  ticker: ticker,
                  name: quote.name,
                  quantity: parseFloat(qty),
                  avg_cost: parseFloat(price),
                }).then(() => {
                  setAddModalOpen(false);
                  navigate("/portfolio");
                }).catch(console.error);
              }}
            >
              Add Holding
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
