import { NavLink } from "react-router-dom";
import { clsx } from "clsx";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: "📊" },
  { path: "/portfolio", label: "Portfolio", icon: "💼" },
  { path: "/watchlist", label: "Watchlist", icon: "👁" },
  { path: "/alerts", label: "Alerts", icon: "🔔" },
  { path: "/settings", label: "Settings", icon: "⚙" },
];

export default function Sidebar() {
  return (
    <aside className="w-16 hover:w-56 bg-surface border-r border-border flex flex-col transition-all duration-200 overflow-hidden shrink-0 group">
      <div className="p-3 border-b border-border">
        <span className="text-xl">📈</span>
        <span className="ml-3 font-bold text-accent-blue opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          FinSight
        </span>
      </div>

      <nav className="flex-1 py-2">
        {NAV_ITEMS.map(({ path, label, icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2.5 mx-1 rounded transition-colors",
                "hover:bg-surface-elevated cursor-pointer",
                isActive && "border-l-[3px] border-accent-blue bg-surface-elevated",
                !isActive && "border-l-[3px] border-transparent"
              )
            }
          >
            <span className="text-lg">{icon}</span>
            <span className="text-sm text-text-secondary opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              {label}
            </span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
