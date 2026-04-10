import WatchlistRow from "./WatchlistRow";
import type { Watchlist } from "../../types";

interface WatchlistPanelProps {
  watchlists: Watchlist[];
  onRemoveItem?: (watchlistId: number, ticker: string) => void;
}

export default function WatchlistPanel({ watchlists, onRemoveItem }: WatchlistPanelProps) {
  const firstList = watchlists[0];

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <span className="text-sm font-medium">Watchlist</span>
        {firstList && (
          <span className="text-xs text-text-secondary">{firstList.name} · {firstList.items.length} items</span>
        )}
      </div>
      <div className="divide-y divide-border max-h-72 overflow-y-auto scrollbar-thin">
        {!firstList || firstList.items.length === 0 ? (
          <div className="px-4 py-6 text-center text-text-secondary text-sm">No items in watchlist</div>
        ) : (
          firstList.items.map((item) => (
            <WatchlistRow
              key={item.ticker}
              item={item}
              onRemove={onRemoveItem ? () => onRemoveItem(firstList.id, item.ticker) : undefined}
            />
          ))
        )}
      </div>
    </div>
  );
}