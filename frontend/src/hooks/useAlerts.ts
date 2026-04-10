import { useState, useEffect, useCallback } from "react";
import { alertsApi } from "../services/api";
import type { Alert } from "../types";

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = useCallback(async () => {
    try {
      const data = await alertsApi.getAll();
      setAlerts(data);
    } catch (err) {
      console.error("Failed to fetch alerts", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const createAlert = async (data: Parameters<typeof alertsApi.create>[0]) => {
    await alertsApi.create(data as any);
    await fetchAlerts();
  };

  const deleteAlert = async (id: number) => {
    await alertsApi.delete(id);
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  const toggleAlert = async (id: number, currentStatus: string) => {
    const newStatus = currentStatus === "active" ? "paused" : "active";
    await alertsApi.update(id, { status: newStatus });
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: newStatus as Alert["status"] } : a))
    );
  };

  return { alerts, loading, createAlert, deleteAlert, toggleAlert, refetch: fetchAlerts };
}