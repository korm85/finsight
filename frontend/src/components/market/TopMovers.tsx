import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Badge from "../ui/Badge";
import { useMarketData } from "../../hooks/useMarketData";
import { Skeleton } from "../ui/Skeleton";

type Tab = "gainers" | "losers" | "most_active";

export default function TopMovers() {
  const [activeTab, setActiveTab] = useState<Tab>("gainers");
  const { gainers, losers, mostActive, loading } = useMarketData();
  const navigate = useNavigate();

  const tabs: { key: Tab; label: string; data: typeof gainers }[] = [
    { key: "gainers", label: "Gainers", data: gainers },
    { key: "losers", label: "Losers", data: losers },
    { key: "most_active", label: "Most Active", data: mostActive },
  ];

  const currentData = tabs.find((t) => t.key === activeTab)?.data || [];

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="flex border-b border-border">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex-1 px-4 py-2.5 text-sm font-medium transition-colors cursor-pointer ${
              activeTab === key
                ? "text-accent-blue border-b-2 border-accent-blue bg-surface-elevated"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="divide-y divide-border max-h-80 overflow-y-auto scrollbar-thin">
        {loading && currentData.length === 0
          ? [...Array(5)].map((_, i) => <Skeleton key={i} className="h-10 mx-4 my-2" />)
          : currentData.slice(0, 10).map((m) => (
              <div
                key={m.ticker}
                className="flex items-center justify-between px-4 py-2.5 hover:bg-surface-elevated cursor-pointer"
                onClick={() => navigate(`/stock/${m.ticker}`)}
              >
                <div>
                  <div className="text-sm font-mono font-medium">{m.ticker}</div>
                  <div className="text-xs text-text-secondary truncate max-w-[120px]">{m.name}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-mono">${m.price?.toFixed(2)}</div>
                  <Badge variant={m.change_pct >= 0 ? "green" : "red"}>
                    {m.change_pct >= 0 ? "+" : ""}{m.change_pct?.toFixed(2)}%
                  </Badge>
                </div>
              </div>
            ))}
      </div>
    </div>
  );
}
