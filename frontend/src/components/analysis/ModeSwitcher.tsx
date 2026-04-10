type Mode = "newbie" | "basic" | "pro";

const MODES: { key: Mode; label: string; icon: string }[] = [
  { key: "newbie", label: "Newbie", icon: "🌱" },
  { key: "basic", label: "Basic", icon: "📊" },
  { key: "pro", label: "Pro", icon: "⚡" },
];

interface ModeSwitcherProps {
  mode: Mode;
  onChange: (mode: Mode) => void;
}

export default function ModeSwitcher({ mode, onChange }: ModeSwitcherProps) {
  return (
    <div className="flex border-b border-border">
      {MODES.map(({ key, label, icon }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className={`flex-1 px-4 py-2.5 text-sm font-medium transition-colors cursor-pointer ${
            mode === key
              ? "text-accent-blue border-b-2 border-accent-blue bg-surface-elevated"
              : "text-text-secondary hover:text-text-primary"
          }`}
        >
          {icon} {label}
        </button>
      ))}
    </div>
  );
}
