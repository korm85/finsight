import { useNavigate } from "react-router-dom";
import Badge from "../ui/Badge";
import type { WatchlistItem } from "../../types";

interface WatchlistRowProps {
  item: WatchlistItem;
  onRemove?: () => void;
}

export default function WatchlistRow({ item, onRemove }: WatchlistRowProps) {
  const navigate = useNavigate();
  const isPositive = item.change_pct >= 0;

  return (
    <div
      className="flex items-center justify-between px-3 py-2 hover:bg-surface-elevated cursor-pointer group"
      onClick={() => navigate(`/stock/${item.ticker}`)}
    >
      <div>
        <div className="font-mono font-medium text-sm">{item.ticker}</div>
        <div className="text-xs text-text-secondary truncate max-w-[100px]">{item.name}</div>
      </div>
      <div className="text-right">
        <div className="font-mono text-sm">${item.price.toFixed(2)}</div>
        <Badge variant={isPositive ? "green" : "red"}>
          {isPositive ? "+" : ""}{item.change_pct.toFixed(2)}%
        </Badge>
      </div>
      {onRemove && (
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className="ml-2 text-text-secondary hover:text-accent-red opacity-0 group-hover:opacity-100 text-xs cursor-pointer"
        >
          ✕
        </button>
      )}
    </div>
  );
}