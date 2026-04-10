import { useState, useEffect } from "react";
import { analysisApi } from "../services/api";
import type { Analysis } from "../types/analysis";

export function useAnalysis(ticker: string) {
  const [data, setData] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    analysisApi.get(ticker)
      .then(setData)
      .catch(() => setError("Analysis unavailable"))
      .finally(() => setLoading(false));
  }, [ticker]);

  return { data, loading, error };
}
