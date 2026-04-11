import PageHeader from "../components/layout/PageHeader";
import AlertList from "../components/alerts/AlertList";
import { useAlerts } from "../hooks/useAlerts";

export default function Alerts() {
  const { alerts, createAlert, deleteAlert, toggleAlert } = useAlerts();

  return (
    <div>
      <PageHeader title="Alerts" subtitle="Get notified when your criteria are met" />
      <AlertList
        alerts={alerts}
        onCreate={async (data) => {
          await createAlert(data);
        }}
        onToggle={(id, status) => toggleAlert(id, status)}
        onDelete={(id) => deleteAlert(id)}
      />
    </div>
  );
}
