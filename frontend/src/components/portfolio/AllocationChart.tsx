import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#2979FF", "#00C853", "#FFD600", "#FF1744", "#9C27B0", "#00BCD4", "#FF9800"];

interface AllocationChartProps {
  holdings: { ticker: string; market_value?: number }[];
}

export default function AllocationChart({ holdings }: AllocationChartProps) {
  const total = holdings.reduce((s, h) => s + (h.market_value ?? 0), 0);
  const data = holdings
    .filter((h) => (h.market_value ?? 0) > 0)
    .map((h) => ({
      name: h.ticker,
      value: h.market_value ?? 0,
      pct: ((h.market_value ?? 0) / total) * 100,
    }))
    .slice(0, 7);

  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      <div className="text-xs text-text-secondary uppercase tracking-wide mb-3">Allocation</div>
      <div className="h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: "#1C2127", border: "1px solid #2A2F38", borderRadius: 8 }}
              formatter={(value: number, name: string) => [`$${value.toLocaleString()}`, name]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="grid grid-cols-2 gap-1 mt-2">
        {data.map((d, i) => (
          <div key={d.name} className="flex items-center gap-1.5 text-xs">
            <div className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
            <span className="text-text-secondary">{d.name}</span>
            <span className="text-text-primary font-mono ml-auto">{d.pct.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
