import { ButtonHTMLAttributes } from "react";
import { clsx } from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
}

export default function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        "rounded font-medium transition-all duration-150 cursor-pointer",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        {
          "bg-accent-blue hover:bg-blue-500 text-white": variant === "primary",
          "bg-surface-elevated hover:bg-border text-text-primary border border-border":
            variant === "secondary",
          "bg-accent-red hover:bg-red-600 text-white": variant === "danger",
          "bg-transparent hover:bg-surface-elevated text-text-secondary hover:text-text-primary":
            variant === "ghost",
        },
        {
          "px-2.5 py-1 text-xs": size === "sm",
          "px-4 py-2 text-sm": size === "md",
          "px-6 py-3 text-base": size === "lg",
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
