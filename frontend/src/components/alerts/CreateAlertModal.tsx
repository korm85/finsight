import { useState } from "react";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import type { AlertCondition } from "../../types";

interface CreateAlertModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: {
    ticker: string; condition: AlertCondition; threshold: number;
    channel_inapp: boolean; channel_email: boolean; channel_push: boolean;
  }) => Promise<void>;
}

const CONDITIONS: { value: AlertCondition; label: string }[] = [
  { value: "price_above", label: "Price Above" },
  { value: "price_below", label: "Price Below" },
  { value: "pct_change_above", label: "% Change Above" },
  { value: "pct_change_below", label: "% Change Below" },
  { value: "volume_above", label: "Volume Above" },
];

export default function CreateAlertModal({ open, onClose, onSubmit }: CreateAlertModalProps) {
  const [ticker, setTicker] = useState("");
  const [condition, setCondition] = useState<AlertCondition>("price_above");
  const [threshold, setThreshold] = useState("");
  const [channelInapp, setChannelInapp] = useState(true);
  const [channelEmail, setChannelEmail] = useState(false);
  const [channelPush, setChannelPush] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!ticker || !threshold) return;
    setLoading(true);
    try {
      await onSubmit({
        ticker: ticker.toUpperCase(),
        condition,
        threshold: parseFloat(threshold),
        channel_inapp: channelInapp,
        channel_email: channelEmail,
        channel_push: channelPush,
      });
      setTicker("");
      setThreshold("");
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Create Alert">
      <div className="space-y-4">
        <div>
          <label className="block text-xs text-text-secondary mb-1">Ticker Symbol</label>
          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="e.g. AAPL"
            className="w-full bg-surface border border-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-blue"
          />
        </div>
        <div>
          <label className="block text-xs text-text-secondary mb-1">Condition</label>
          <select
            value={condition}
            onChange={(e) => setCondition(e.target.value as AlertCondition)}
            className="w-full bg-surface border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-blue"
          >
            {CONDITIONS.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-text-secondary mb-1">Threshold</label>
          <input
            type="number"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            placeholder={condition.includes("pct") ? "e.g. 5" : "e.g. 200.00"}
            className="w-full bg-surface border border-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-blue"
          />
        </div>
        <div>
          <label className="block text-xs text-text-secondary mb-2">Notify via</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" checked={channelInapp} onChange={(e) => setChannelInapp(e.target.checked)} />
              In-app
            </label>
            <label className="flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" checked={channelEmail} onChange={(e) => setChannelEmail(e.target.checked)} />
              Email
            </label>
            <label className="flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" checked={channelPush} onChange={(e) => setChannelPush(e.target.checked)} />
              Browser
            </label>
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={loading || !ticker || !threshold}>
            {loading ? "Creating..." : "Create Alert"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
