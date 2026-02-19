/**
 * EmptyStatePanel.tsx (v4.74.0 - Wave 33)
 *
 * Standardised empty-state display used when a list or table has no data.
 * data-testid: empty-state-panel
 */
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface EmptyStatePanelProps {
  title?: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EmptyStatePanel({
  title = "No data",
  description = "There is nothing here yet.",
  icon,
  action,
  className,
}: EmptyStatePanelProps) {
  return (
    <div
      data-testid="empty-state-panel"
      className={cn(
        "flex flex-col items-center justify-center gap-3 py-16 text-center",
        className
      )}
    >
      {icon && (
        <div className="text-muted-foreground opacity-40 mb-2">{icon}</div>
      )}
      <p className="text-base font-medium text-foreground">{title}</p>
      <p className="text-sm text-muted-foreground max-w-xs">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export default EmptyStatePanel;
