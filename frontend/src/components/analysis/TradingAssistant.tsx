import ModeSwitcher from "./ModeSwitcher";
import PlainEnglishCard from "./PlainEnglishCard";
import TechnicalCard from "./TechnicalCard";
import FundamentalsCard from "./FundamentalsCard";
import { useAnalysis } from "../../hooks/useAnalysis";
import { Skeleton } from "../ui/Skeleton";

export type AnalysisMode = "newbie" | "basic" | "pro";

interface TradingAssistantProps {
  ticker: string;
  mode: AnalysisMode;
  onModeChange: (mode: AnalysisMode) => void;
}

export default function TradingAssistant({ ticker, mode, onModeChange }: TradingAssistantProps) {
  const { data, loading, error } = useAnalysis(ticker);

  if (loading) {
    return (
      <div className="space-y-0">
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <div className="h-10 bg-surface-elevated border-b border-border" />
          <div className="grid grid-cols-1 lg:grid-cols-3">
            <div className="p-4 border-b lg:border-b-0 lg:border-r border-border"><Skeleton className="h-40 rounded" /></div>
            <div className="p-4 border-b lg:border-b-0 lg:border-r border-border"><Skeleton className="h-40 rounded" /></div>
            <div className="p-4"><Skeleton className="h-40 rounded" /></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-surface border border-border rounded-lg p-6 text-center text-text-secondary text-sm">
        Analysis unavailable for {ticker}
      </div>
    );
  }

  return (
    <div className="space-y-0">
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <ModeSwitcher mode={mode} onChange={onModeChange} />
        <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-border">
          <PlainEnglishCard data={data} mode={mode} />
          <TechnicalCard data={data} />
          <FundamentalsCard data={data} />
        </div>
      </div>
    </div>
  );
}