import { createContext, useContext, useState, ReactNode, useCallback } from "react";
import { clsx } from "clsx";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({ showToast: () => {} });

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = "info") => {
    const id = Date.now();
    setToasts((prev) => [...prev.slice(-2), { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const removeToast = (id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={clsx(
              "px-4 py-3 rounded-lg shadow-lg min-w-[280px] max-w-[400px]",
              "border-l-4 bg-surface-elevated",
              {
                "border-accent-green": toast.type === "success",
                "border-accent-red": toast.type === "error",
                "border-accent-blue": toast.type === "info",
                "border-accent-gold": toast.type === "warning",
              }
            )}
            onClick={() => removeToast(toast.id)}
          >
            <span className="text-sm text-text-primary">{toast.message}</span>
          </div>
        ))}
      </div>
      {children}
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
