import type { Analysis, Recommendation } from "../../types/analysis";
import Badge from "../ui/Badge";

const RECOMMENDATION_CONFIG: Record<Recommendation, { label: string; variant: "green" | "gold" | "red" }> = {
  strong_buy: { label: "STRONG BUY", variant: "green" },
  buy: { label: "BUY", variant: "green" },
  hold: { label: "HOLD", variant: "gold" },
  sell: { label: "SELL", variant: "red" },
  strong_sell: { label: "STRONG SELL", variant: "red" },
};

interface PlainEnglishCardProps {
  data: Analysis;
  mode: "newbie" | "basic" | "pro";
}

export default function PlainEnglishCard({ data, mode }: PlainEnglishCardProps) {
  const rec = RECOMMENDATION_CONFIG[data.recommendation];
  const text = data.plain_english[mode];

  const scoreColor = data.score >= 7 ? "#3fb950" : data.score >= 5 ? "#d29922" : "#f85149";

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border">
        <span className="text-base">📝</span>
        <span className="text-xs font-semibold uppercase tracking-wide text-text-secondary">Plain English</span>
        <Badge variant={rec.variant} className="ml-auto">{rec.label}</Badge>
      </div>
      <div className="p-4">
        <p className="text-sm text-text-primary leading-relaxed mb-4">{text}</p>
        <div className="mb-1">
          <div className="flex justify-between text-xs text-text-secondary mb-1.5">
            <span>Score</span>
            <span style={{ color: scoreColor, fontFamily: "monospace", fontWeight: 600 }}>
              {data.score.toFixed(1)} / 10
            </span>
          </div>
          <div className="h-2 bg-border rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${data.score * 10}%`,
                background: `linear-gradient(90deg, #f85149 0%, #d29922 50%, #3fb950 100%)`,
              }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-text-secondary mt-1">
            <span>← Strong Sell</span>
            <span>Strong Buy →</span>
          </div>
        </div>
      </div>
    </div>
  );
}