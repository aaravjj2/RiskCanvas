/**
 * ErrorPanel.tsx (v4.74.0 - Wave 33)
 *
 * Deterministic error display panel.
 * data-testid: error-panel
 */
import { cn } from "@/lib/utils";

interface ErrorPanelProps {
  message: string;
  detail?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorPanel({ message, detail, onRetry, className }: ErrorPanelProps) {
  return (
    <div
      data-testid="error-panel"
      className={cn(
        "flex flex-col gap-2 p-4 rounded-md border border-destructive/30 bg-destructive/5",
        className
      )}
    >
      <p className="text-sm font-semibold text-destructive">{message}</p>
      {detail && (
        <p className="text-xs text-muted-foreground font-mono">{detail}</p>
      )}
      {onRetry && (
        <button
          data-testid="error-panel-retry"
          onClick={onRetry}
          className="mt-1 self-start text-xs underline text-primary"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export default ErrorPanel;
