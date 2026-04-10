import { useEffect, useRef } from "react";

type RefreshFn = () => void | Promise<void>;

export function useAutoRefresh(refresh: RefreshFn, intervalMs: number) {
  const savedRefresh = useRef<RefreshFn>(refresh);
  savedRefresh.current = refresh;

  useEffect(() => {
    if (intervalMs <= 0) return;

    const id = setInterval(() => {
      savedRefresh.current();
    }, intervalMs);

    return () => clearInterval(id);
  }, [intervalMs]);
}
