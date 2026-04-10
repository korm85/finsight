import { useState } from "react";
import AlertRuleCard from "./AlertRuleCard";
import CreateAlertModal from "./CreateAlertModal";
import Button from "../ui/Button";
import type { Alert, AlertCondition } from "../../types";

interface AlertListProps {
  alerts: Alert[];
  onCreate: (data: {
    ticker: string; condition: AlertCondition; threshold: number;
    channel_inapp: boolean; channel_email: boolean; channel_push: boolean;
  }) => Promise<void>;
  onToggle: (id: number, status: string) => void;
  onDelete: (id: number) => void;
}

export default function AlertList({ alerts, onCreate, onToggle, onDelete }: AlertListProps) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Alert Rules</h2>
        <Button onClick={() => setModalOpen(true)}>+ New Alert</Button>
      </div>
      <div className="space-y-3">
        {alerts.length === 0 ? (
          <div className="bg-surface border border-border rounded-lg p-8 text-center text-text-secondary">
            No alerts yet. Create one to get notified when your criteria are met.
          </div>
        ) : (
          alerts.map((alert) => (
            <AlertRuleCard
              key={alert.id}
              alert={alert}
              onToggle={() => onToggle(alert.id, alert.status)}
              onDelete={() => onDelete(alert.id)}
            />
          ))
        )}
      </div>
      <CreateAlertModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={onCreate}
      />
    </div>
  );
}
