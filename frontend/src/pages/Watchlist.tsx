import { useState, useEffect, useCallback } from "react";
import PageHeader from "../components/layout/PageHeader";
import WatchlistRow from "../components/watchlist/WatchlistRow";
import Modal from "../components/ui/Modal";
import Button from "../components/ui/Button";
import { useAutoRefresh } from "../hooks/useAutoRefresh";
import { watchlistApi } from "../services/api";
import type { Watchlist } from "../types";

const REFRESH_INTERVAL = 10_000; // 10 seconds

export default function Watchlist() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");

  const load = useCallback(() => watchlistApi.getAll().then(setWatchlists).catch(console.error), []);

  useEffect(() => { load(); }, [load]);
  useAutoRefresh(load, REFRESH_INTERVAL);

  useEffect(() => { load(); }, []);

  return (
    <div>
      <PageHeader
        title="Watchlists"
        subtitle="Track your favourite tickers"
        action={<Button onClick={() => setCreateOpen(true)}>+ New Watchlist</Button>}
      />
      <div className="space-y-6">
        {watchlists.length === 0 ? (
          <div className="bg-surface border border-border rounded-lg p-8 text-center text-text-secondary">
            No watchlists yet. Create one to start tracking tickers.
          </div>
        ) : (
          watchlists.map((wl) => (
            <div key={wl.id} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <span className="font-medium">{wl.name}</span>
                <span className="text-xs text-text-secondary">{wl.items.length} items</span>
              </div>
              <div className="divide-y divide-border">
                {wl.items.length === 0 ? (
                  <div className="px-4 py-4 text-center text-text-secondary text-sm">Empty watchlist</div>
                ) : (
                  wl.items.map((item) => (
                    <WatchlistRow
                      key={item.ticker}
                      item={item}
                      onRemove={() => {
                        watchlistApi.removeItem(wl.id, item.ticker).then(load);
                      }}
                    />
                  ))
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="New Watchlist">
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-text-secondary mb-1">Name</label>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full bg-surface border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-blue"
              placeholder="e.g. Tech Stocks"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button
              onClick={async () => {
                if (!newName) return;
                await watchlistApi.create(newName);
                setCreateOpen(false);
                setNewName("");
                load();
              }}
            >
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
