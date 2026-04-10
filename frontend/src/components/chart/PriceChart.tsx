import { useEffect, useRef, useState } from "react";
import { createChart, IChartApi, ISeriesApi, CandlestickData } from "lightweight-charts";
import { marketApi } from "../../services/api";
import { Skeleton } from "../ui/Skeleton";

interface PriceChartProps {
  ticker: string;
  initialRange?: string;
}

export default function PriceChart({ ticker, initialRange = "1M" }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [range, setRange] = useState(initialRange);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: "#13171C" },
        textColor: "#8B9199",
      },
      grid: {
        vertLines: { color: "#2A2F38" },
        horzLines: { color: "#2A2F38" },
      },
      crosshair: {
        mode: 1,
        vertLine: { color: "#2979FF", width: 1, style: 2 },
        horzLine: { color: "#2979FF", width: 1, style: 2 },
      },
      timeScale: {
        borderColor: "#2A2F38",
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: "#2A2F38",
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#00C853",
      downColor: "#FF1744",
      borderUpColor: "#00C853",
      borderDownColor: "#FF1744",
      wickUpColor: "#00C853",
      wickDownColor: "#FF1744",
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    setLoading(true);
    marketApi.chart(ticker, range)
      .then((data) => {
        if (data?.candles && candleSeriesRef.current) {
          const chartData: CandlestickData[] = data.candles.map((c: any) => ({
            time: c.time as number,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
          }));
          candleSeriesRef.current.setData(chartData);
          chartRef.current?.timeScale().fitContent();
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [ticker, range]);

  const timeframes = ["1D", "1W", "1M", "3M", "1Y", "MAX"] as const;

  return (
    <div>
      <div className="flex items-center gap-1 mb-3">
        {timeframes.map((tf) => (
          <button
            key={tf}
            onClick={() => setRange(tf)}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
              range === tf
                ? "bg-accent-blue text-white"
                : "bg-surface-elevated text-text-secondary hover:text-text-primary"
            }`}
          >
            {tf}
          </button>
        ))}
      </div>
      <div ref={containerRef} className="w-full h-[400px] relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-surface/80">
            <Skeleton className="w-full h-full" />
          </div>
        )}
      </div>
    </div>
  );
}
