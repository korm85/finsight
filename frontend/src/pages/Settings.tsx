import { useState, useEffect } from "react";
import PageHeader from "../components/layout/PageHeader";
import Button from "../components/ui/Button";
import { settingsApi } from "../services/api";

type SettingsState = {
  display_name: string;
  email: string;
  email_notifications: boolean;
  push_notifications: boolean;
  refresh_rate: number;
};

export default function Settings() {
  const [settings, setSettings] = useState({
    display_name: "Investor",
    email: "",
    email_notifications: true,
    push_notifications: false,
    refresh_rate: 60,
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    settingsApi.get().then((s: SettingsState) => setSettings(s)).catch(console.error);
  }, []);

  const handleSave = async () => {
    await settingsApi.update(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div>
      <PageHeader title="Settings" subtitle="Customize your experience" />
      <div className="max-w-xl space-y-6">
        <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
          <h2 className="font-semibold">Profile</h2>
          <div>
            <label className="block text-xs text-text-secondary mb-1">Display Name</label>
            <input
              value={settings.display_name}
              onChange={(e) => setSettings({ ...settings, display_name: e.target.value })}
              className="w-full bg-surface-elevated border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-blue"
            />
          </div>
          <div>
            <label className="block text-xs text-text-secondary mb-1">Email (for alerts)</label>
            <input
              value={settings.email || ""}
              onChange={(e) => setSettings({ ...settings, email: e.target.value })}
              className="w-full bg-surface-elevated border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-blue"
              placeholder="you@example.com"
            />
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
          <h2 className="font-semibold">Notifications</h2>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.email_notifications}
              onChange={(e) => setSettings({ ...settings, email_notifications: e.target.checked })}
            />
            <span className="text-sm">Email notifications</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.push_notifications}
              onChange={(e) => setSettings({ ...settings, push_notifications: e.target.checked })}
            />
            <span className="text-sm">Browser push notifications</span>
          </label>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
          <h2 className="font-semibold">Data Refresh Rate</h2>
          <select
            value={settings.refresh_rate}
            onChange={(e) => setSettings({ ...settings, refresh_rate: parseInt(e.target.value) })}
            className="bg-surface-elevated border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-blue"
          >
            <option value={30}>Every 30 seconds</option>
            <option value={60}>Every 1 minute</option>
            <option value={300}>Every 5 minutes</option>
          </select>
        </div>

        <Button onClick={handleSave}>{saved ? "Saved!" : "Save Settings"}</Button>
      </div>
    </div>
  );
}
