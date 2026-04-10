import Badge from "../ui/Badge";
import type { Alert } from "../../types";

const CONDITION_LABELS: Record<string, string> = {
  price_above: "Price Above",
  price_below: "Price Below",
  price_crosses: "Price Crosses",
  pct_change_above: "% Change Above",
  pct_change_below: "% Change Below",
  volume_above: "Volume Above",
  earnings_within: "Earnings Within",
};

interface AlertRuleCardProps {
  alert: Alert;
  onToggle: () => void;
  onDelete: () => void;
}

export default function AlertRuleCard({ alert, onToggle, onDelete }: AlertRuleCardProps) {
  return (
    <div
      className={`bg-surface border rounded-lg p-4 ${
        alert.status === "triggered" ? "border-accent-gold" : "border-border"
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="font-mono font-bold text-lg">{alert.ticker}</div>
          <div className="text-sm text-text-secondary mt-0.5">
            {CONDITION_LABELS[alert.condition] || alert.condition} ·{" "}
            <span className="font-mono">
              {alert.condition.includes("pct") || alert.condition.includes("volume")
                ? `${alert.threshold}%`
                : `$${alert.threshold.toFixed(2)}`}
            </span>
          </div>
          <div className="flex gap-1 mt-2">
            {alert.channel_inapp && <Badge variant="blue">In-app</Badge>}
            {alert.channel_email && <Badge variant="neutral">Email</Badge>}
            {alert.channel_push && <Badge variant="gold">Push</Badge>}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Badge
            variant={alert.status === "active" ? "green" : alert.status === "triggered" ? "gold" : "neutral"}
          >
            {alert.status}
          </Badge>
          <div className="flex gap-1">
            <button onClick={onToggle} className="text-xs text-text-secondary hover:text-accent-blue cursor-pointer">
              {alert.status === "active" ? "⏸" : "▶"}
            </button>
            <button onClick={onDelete} className="text-xs text-text-secondary hover:text-accent-red cursor-pointer">
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
