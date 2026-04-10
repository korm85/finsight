import { clsx } from "clsx";

interface BadgeProps {
  variant?: "green" | "red" | "neutral" | "gold" | "blue";
  children: React.ReactNode;
  className?: string;
}

export default function Badge({ variant = "neutral", children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium font-mono",
        {
          "bg-accent-green/20 text-accent-green": variant === "green",
          "bg-accent-red/20 text-accent-red": variant === "red",
          "bg-surface-elevated text-text-secondary border border-border": variant === "neutral",
          "bg-accent-gold/20 text-accent-gold": variant === "gold",
          "bg-accent-blue/20 text-accent-blue": variant === "blue",
        },
        className
      )}
    >
      {children}
    </span>
  );
}
