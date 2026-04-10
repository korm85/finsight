import { useMarketData } from "../../hooks/useMarketData";
import IndexCard from "./IndexCard";
import { Skeleton } from "../ui/Skeleton";

export default function MarketOverview() {
  const { indices, loading } = useMarketData();

  if (loading && indices.length === 0) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-28 rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {indices.map((idx) => (
        <IndexCard key={idx.symbol} data={idx} />
      ))}
    </div>
  );
}
