import type { Analysis, FundamentalData } from "../../types/analysis";

const TOOLTIPS: Record<string, string> = {
  pe_ratio: "How expensive the stock is relative to earnings. Higher = more expensive. Compare to sector average.",
  vs_sector: "Is this stock cheaper or pricier than similar companies? Lower than average = potentially good value.",
  market_cap: "Total value of all shares. Mega = over $200B (very established). Small = under $2B (riskier).",
  dividend: "A company pays you to own its stock. Growth stocks usually pay little — they reinvest profits instead.",
  beta: "How much the stock moves compared to the overall market. Above 1 = more risky but potentially higher returns.",
  range_52w: "Shows if the stock is near its high (less upside) or low (more upside potential) over the past year.",
};

function getVerdicts(f: FundamentalData) {
  const pe = f.pe_verdict === "cheaper_than_avg" ? "Cheaper than avg" : f.pe_verdict === "expensive" ? "Expensive" : "Fair value";
  const peColor = f.pe_verdict === "cheaper_than_avg" ? "#3fb950" : f.pe_verdict === "expensive" ? "#f85149" : "#d29922";
  const betaLabel = f.beta_verdict ? f.beta_verdict.charAt(0).toUpperCase() + f.beta_verdict.slice(1) + " volatility" : "N/A";
  const rangeLabel = f.fiftytwo_week_range_verdict === "near_low" ? "Near 52W low" : f.fiftytwo_week_range_verdict === "near_high" ? "Near 52W high" : "Mid range";
  const rangeColor = f.fiftytwo_week_range_verdict === "near_low" ? "#3fb950" : f.fiftytwo_week_range_verdict === "near_high" ? "#f85149" : "#d29922";
  const verdictBg = f.verdict_text.includes("strong momentum") || f.verdict_text.includes("cheaper") ? "#0d4426"
    : f.verdict_text.includes("pricier") || f.verdict_text.includes("near high") ? "#4d1010"
    : "#3d3020";
  const verdictColor = f.verdict_text.includes("strong momentum") || f.verdict_text.includes("cheaper") ? "#3fb950"
    : f.verdict_text.includes("pricier") || f.verdict_text.includes("near high") ? "#f85149"
    : "#d29922";
  return { pe, peColor, betaLabel, rangeLabel, rangeColor, verdictBg, verdictColor };
}

export default function FundamentalsCard({ data }: { data: Analysis }) {
  const f = data.fundamental;
  const v = getVerdicts(f);

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border">
        <span className="text-base">💰</span>
        <span className="text-xs font-semibold uppercase tracking-wide text-text-secondary">Fundamentals</span>
        <span
          className="ml-auto text-xs font-medium px-2 py-0.5 rounded-full"
          style={{ background: f.pe_verdict === "cheaper_than_avg" ? "#0d4426" : f.pe_verdict === "expensive" ? "#4d1010" : "#3d3020", color: v.peColor }}
        >
          {v.pe}
        </span>
      </div>
      <div className="p-4">
        {/* P/E Ratio */}
        <div className="flex justify-between items-center py-2 border-b border-border">
          <div className="flex items-center gap-1">
            <span className="text-xs text-text-secondary">P/E Ratio</span>
            <span className="text-[10px] text-text-secondary cursor-help border-b border-dashed border-text-secondary" title={TOOLTIPS.pe_ratio}>?</span>
          </div>
          <span className="text-xs font-mono text-text-primary">{f.pe_ratio != null ? f.pe_ratio.toFixed(1) : "N/A"}</span>
        </div>
        {/* vs Sector */}
        <div className="flex justify-between items-center py-2 border-b border-border">
          <div className="flex items-center gap-1">
            <span className="text-xs text-text-secondary">vs Sector</span>
            <span className="text-[10px] text-text-secondary cursor-help border-b border-dashed border-text-secondary" title={TOOLTIPS.vs_sector}>?</span>
          </div>
          <div className="text-right">
            <span className="text-xs font-mono" style={{ color: v.peColor }}>{v.pe}</span>
            <div className="text-[10px] text-text-secondary">{f.sector_pe_median ? `Sector avg: ${f.sector_pe_median.toFixed(0)}` : ""}</div>
          </div>
        </div>
        {/* Market Cap */}
        <div className="flex justify-between items-center py-2 border-b border-border">
          <div className="flex items-center gap-1">
            <span className="text-xs text-text-secondary">Market Cap</span>
            <span className="text-[10px] text-text-secondary cursor-help border-b border-dashed border-text-secondary" title={TOOLTIPS.market_cap}>?</span>
          </div>
          <span className="text-xs font-mono text-text-primary">{f.market_cap_label || "N/A"}</span>
        </div>
        {/* Dividend */}
        <div className="flex justify-between items-center py-2 border-b border-border">
          <div className="flex items-center gap-1">
            <span className="text-xs text-text-secondary">Dividend</span>
            <span className="text-[10px] text-text-secondary cursor-help border-b border-dashed border-text-secondary" title={TOOLTIPS.dividend}>?</span>
          </div>
          <span className="text-xs font-mono text-text-primary">{f.dividend_yield != null ? `${(f.dividend_yield * 100).toFixed(2)}%` : "N/A"}</span>
        </div>
        {/* Beta */}
        <div className="flex justify-between items-center py-2 border-b border-border">
          <div className="flex items-center gap-1">
            <span className="text-xs text-text-secondary">Beta</span>
            <span className="text-[10px] text-text-secondary cursor-help border-b border-dashed border-text-secondary" title={TOOLTIPS.beta}>?</span>
          </div>
          <div className="text-right">
            <span className="text-xs font-mono text-text-primary">{f.beta != null ? f.beta.toFixed(2) : "N/A"}</span>
            <div className="text-[10px] text-text-secondary">{v.betaLabel}</div>
          </div>
        </div>
        {/* 52W Range */}
        <div className="flex justify-between items-center py-2 border-b border-border">
          <div className="flex items-center gap-1">
            <span className="text-xs text-text-secondary">52W Range</span>
            <span className="text-[10px] text-text-secondary cursor-help border-b border-dashed border-text-secondary" title={TOOLTIPS.range_52w}>?</span>
          </div>
          <span className="text-xs font-mono" style={{ color: v.rangeColor }}>{v.rangeLabel}</span>
        </div>
        {/* Verdict */}
        <div
          className="mt-3 p-3 rounded-md text-xs"
          style={{ background: v.verdictBg, color: v.verdictColor }}
        >
          ✓ {f.verdict_text}
        </div>
      </div>
    </div>
  );
}