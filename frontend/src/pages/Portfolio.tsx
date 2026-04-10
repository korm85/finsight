import { useState, useEffect, useCallback } from "react";
import PageHeader from "../components/layout/PageHeader";
import PortfolioSummary from "../components/portfolio/PortfolioSummary";
import HoldingsTable from "../components/portfolio/HoldingsTable";
import AllocationChart from "../components/portfolio/AllocationChart";
import Modal from "../components/ui/Modal";
import Button from "../components/ui/Button";
import { useAutoRefresh } from "../hooks/useAutoRefresh";
import { portfolioApi } from "../services/api";
import type { Portfolio } from "../types";

const REFRESH_INTERVAL = 10_000; // 10 seconds

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState({ ticker: "", qty: "", price: "" });

  const load = useCallback(() => portfolioApi.get().then(setPortfolio).catch(console.error), []);

  useEffect(() => { load(); }, [load]);
  useAutoRefresh(load, REFRESH_INTERVAL);

  const handleDelete = async (id: number) => {
    await portfolioApi.deleteHolding(id);
    load();
  };

  return (
    <div>
      <PageHeader
        title="Portfolio"
        subtitle="Manage your holdings"
        action={<Button onClick={() => setAddOpen(true)}>+ Add Holding</Button>}
      />
      {portfolio && (
        <div className="space-y-6">
          <PortfolioSummary portfolio={portfolio} />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <HoldingsTable holdings={portfolio.holdings} onDelete={handleDelete} />
            </div>
            <AllocationChart holdings={portfolio.holdings} />
          </div>
        </div>
      )}

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add Holding">
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-text-secondary mb-1">Ticker</label>
            <input
              value={form.ticker}
              onChange={(e) => setForm({ ...form, ticker: e.target.value.toUpperCase() })}
              className="w-full bg-surface border border-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-blue"
              placeholder="e.g. AAPL"
            />
          </div>
          <div>
            <label className="block text-xs text-text-secondary mb-1">Quantity</label>
            <input
              type="number"
              value={form.qty}
              onChange={(e) => setForm({ ...form, qty: e.target.value })}
              className="w-full bg-surface border border-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-blue"
              placeholder="e.g. 10"
            />
          </div>
          <div>
            <label className="block text-xs text-text-secondary mb-1">Avg Cost ($)</label>
            <input
              type="number"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
              className="w-full bg-surface border border-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-blue"
              placeholder="e.g. 150.00"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setAddOpen(false)}>Cancel</Button>
            <Button
              onClick={async () => {
                if (!form.ticker || !form.qty || !form.price) return;
                await portfolioApi.addHolding({
                  ticker: form.ticker,
                  name: form.ticker,
                  quantity: parseFloat(form.qty),
                  avg_cost: parseFloat(form.price),
                });
                setAddOpen(false);
                setForm({ ticker: "", qty: "", price: "" });
                load();
              }}
            >
              Add
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
