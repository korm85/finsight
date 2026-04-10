import type { Portfolio } from "../../types";

interface PortfolioSummaryProps {
  portfolio: Portfolio;
}

export default function PortfolioSummary({ portfolio }: PortfolioSummaryProps) {
  const isPositive = portfolio.day_pnl >= 0;
  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      <div className="text-xs text-text-secondary uppercase tracking-wide mb-3">Portfolio Value</div>
      <div className="text-3xl font-bold font-mono text-text-primary mb-4">
        ${portfolio.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <div className="text-xs text-text-secondary">Total P&L</div>
          <div className={`text-sm font-mono font-medium ${portfolio.total_pnl >= 0 ? "text-accent-green" : "text-accent-red"}`}>
            {portfolio.total_pnl >= 0 ? "+" : ""}${portfolio.total_pnl.toFixed(2)}
            <span className="ml-1 text-xs">({portfolio.total_pnl_pct.toFixed(2)}%)</span>
          </div>
        </div>
        <div>
          <div className="text-xs text-text-secondary">Cost Basis</div>
          <div className="text-sm font-mono text-text-primary">
            ${portfolio.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div>
          <div className="text-xs text-text-secondary">Day P&L</div>
          <div className={`text-sm font-mono font-medium ${isPositive ? "text-accent-green" : "text-accent-red"}`}>
            {isPositive ? "+" : ""}${portfolio.day_pnl.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}
