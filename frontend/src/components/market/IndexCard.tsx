import { LineChart, Line, ResponsiveContainer } from "recharts";
import Badge from "../ui/Badge";
import type { IndexQuote } from "../../types";

interface IndexCardProps {
  data: IndexQuote;
}

export default function IndexCard({ data }: IndexCardProps) {
  const isPositive = data.change >= 0;
  return (
    <div className="bg-surface border border-border rounded-lg p-4 hover:bg-surface-elevated transition-colors cursor-pointer">
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="text-xs text-text-secondary font-medium">{data.name}</div>
          <div className="text-lg font-bold font-mono mt-0.5">
            {data.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <Badge variant={isPositive ? "green" : "red"}>
          {isPositive ? "+" : ""}{data.change_pct.toFixed(2)}%
        </Badge>
      </div>
      {data.sparkline.length > 0 && (
        <ResponsiveContainer width="100%" height={40}>
          <LineChart data={data.sparkline.map((v, i) => ({ i, v }))}>
            <Line
              type="monotone"
              dataKey="v"
              stroke={isPositive ? "#00C853" : "#FF1744"}
              strokeWidth={1.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}