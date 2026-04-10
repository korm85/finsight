interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  showDot?: boolean;
}

export default function Sparkline({
  data,
  width = 60,
  height = 24,
  color = "#2979FF",
  showDot = false,
}: SparklineProps) {
  if (data.length < 2) return <div style={{ width, height }} />;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pad = 2;

  const points = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (width - pad * 2);
    const y = pad + (1 - (v - min) / range) * (height - pad * 2);
    return `${x},${y}`;
  });

  const lastX = pad + (width - pad * 2);
  const lastY = pad + (1 - (data[data.length - 1] - min) / range) * (height - pad * 2);

  return (
    <svg width={width} height={height} style={{ overflow: "visible" }}>
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {showDot && (
        <circle cx={lastX} cy={lastY} r="2.5" fill={color} />
      )}
    </svg>
  );
}
