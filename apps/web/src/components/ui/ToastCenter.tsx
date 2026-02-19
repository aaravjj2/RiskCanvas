/**
 * ToastCenter.tsx (v4.77.0 - Wave 33)
 *
 * Deterministic toast notification system.
 * - Context provider wraps app
 * - useToast() hook adds/removes toasts
 * - Messages have fixed copy (no randomness)
 *
 * data-testids:
 *   toast-center, toast-item-{i}, toast-close-{i}
 */
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { cn } from "@/lib/utils";
import { X, CheckCircle2, AlertCircle, Info } from "lucide-react";

export type ToastVariant = "success" | "error" | "info";

export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  addToast: (message: string, variant?: ToastVariant) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

let _counter = 0;
const genId = () => `toast-${++_counter}`;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const dismiss = useCallback((id: string) => {
    clearTimeout(timers.current[id]);
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback(
    (message: string, variant: ToastVariant = "info") => {
      const id = genId();
      setToasts(prev => [...prev, { id, message, variant }]);
      timers.current[id] = setTimeout(() => dismiss(id), 4200);
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={{ addToast, dismiss }}>
      {children}
      {/* Toast container */}
      <div
        data-testid="toast-center"
        className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none"
      >
        {toasts.map((t, i) => (
          <ToastItem
            key={t.id}
            toast={t}
            index={i}
            onDismiss={() => dismiss(t.id)}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastItem({
  toast,
  index,
  onDismiss,
}: {
  toast: Toast;
  index: number;
  onDismiss: () => void;
}) {
  const Icon =
    toast.variant === "success"
      ? CheckCircle2
      : toast.variant === "error"
        ? AlertCircle
        : Info;

  const colorCls =
    toast.variant === "success"
      ? "border-green-200 bg-green-50 text-green-800"
      : toast.variant === "error"
        ? "border-red-200 bg-red-50 text-red-800"
        : "border-blue-200 bg-blue-50 text-blue-800";

  return (
    <div
      data-testid={`toast-item-${index}`}
      className={cn(
        "pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg border shadow-md text-sm min-w-[280px] max-w-sm",
        colorCls
      )}
    >
      <Icon className="h-4 w-4 flex-shrink-0" />
      <span className="flex-1">{toast.message}</span>
      <button
        data-testid={`toast-close-${index}`}
        onClick={onDismiss}
        aria-label="Dismiss toast"
        className="p-0.5 rounded hover:opacity-70"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
}

export default ToastProvider;
