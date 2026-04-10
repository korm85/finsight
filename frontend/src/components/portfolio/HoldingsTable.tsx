import { useNavigate } from "react-router-dom";
import Badge from "../ui/Badge";
import type { Holding } from "../../types";

interface HoldingsTableProps {
  holdings: Holding[];
  onDelete: (id: number) => void;
}

export default function HoldingsTable({ holdings, onDelete }: HoldingsTableProps) {
  const navigate = useNavigate();

  if (holdings.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-8 text-center">
        <div className="text-text-secondary mb-4">No holdings yet. Add your first position.</div>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-surface-elevated border-b border-border">
          <tr>
            {["Ticker", "Qty", "Avg Cost", "Current", "Market Value", "P&L", "P&L %"].map((col) => (
              <th key={col} className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wide">
                {col}
              </th>
            ))}
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {holdings.map((h) => {
            const pnlPos = (h.pnl ?? 0) >= 0;
            return (
              <tr
                key={h.id}
                className="hover:bg-surface-elevated cursor-pointer"
                onClick={() => navigate(`/stock/${h.ticker}`)}
              >
                <td className="px-4 py-3">
                  <div className="font-mono font-medium">{h.ticker}</div>
                  <div className="text-xs text-text-secondary truncate max-w-[120px]">{h.name}</div>
                </td>
                <td className="px-4 py-3 font-mono">{h.quantity}</td>
                <td className="px-4 py-3 font-mono">${h.avg_cost.toFixed(2)}</td>
                <td className="px-4 py-3 font-mono">${(h.current_price ?? 0).toFixed(2)}</td>
                <td className="px-4 py-3 font-mono">${(h.market_value ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td className={`px-4 py-3 font-mono font-medium ${pnlPos ? "text-accent-green" : "text-accent-red"}`}>
                  {pnlPos ? "+" : ""}${(h.pnl ?? 0).toFixed(2)}
                </td>
                <td className="px-4 py-3">
                  <Badge variant={pnlPos ? "green" : "red"}>
                    {pnlPos ? "+" : ""}{(h.pnl_pct ?? 0).toFixed(2)}%
                  </Badge>
                </td>
                <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => onDelete(h.id)}
                    className="text-text-secondary hover:text-accent-red text-xs cursor-pointer"
                  >
                    ✕
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
