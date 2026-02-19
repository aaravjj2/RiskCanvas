/**
 * PageShell.tsx (v4.74.0 - Wave 33)
 *
 * Standard page wrapper used by every route page.
 * Provides consistent layout: title bar, actions slots, status bar, content area.
 *
 * data-testids:
 *   page-shell, page-title, page-subtitle, page-actions,
 *   page-secondary-actions, page-statusbar, page-content
 */
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface PageShellProps {
  /** Page heading */
  title: string;
  /** Optional subtitle / wave label */
  subtitle?: string;
  /** Primary action buttons (right-aligned in header) */
  actions?: ReactNode;
  /** Secondary action area (below/beside primary) */
  secondaryActions?: ReactNode;
  /** Status bar content (hashes, env, mode flags) */
  statusBar?: ReactNode;
  /** Main page body */
  children: ReactNode;
  className?: string;
  /** Extra testid suffix for disambiguation */
  testId?: string;
}

export function PageShell({
  title,
  subtitle,
  actions,
  secondaryActions,
  statusBar,
  children,
  className,
  testId,
}: PageShellProps) {
  const shellId = testId ? `page-shell-${testId}` : "page-shell";

  return (
    <div
      data-testid={shellId}
      className={cn("flex flex-col gap-0 min-h-full", className)}
    >
      {/* Header bar */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-border mb-6">
        <div className="flex flex-col gap-1 min-w-0">
          <h1
            data-testid="page-title"
            className="text-2xl font-bold leading-tight tracking-tight truncate"
          >
            {title}
          </h1>
          {subtitle && (
            <p
              data-testid="page-subtitle"
              className="text-sm text-muted-foreground"
            >
              {subtitle}
            </p>
          )}
          {secondaryActions && (
            <div data-testid="page-secondary-actions" className="mt-2 flex gap-2 flex-wrap">
              {secondaryActions}
            </div>
          )}
        </div>
        {actions && (
          <div
            data-testid="page-actions"
            className="flex items-center gap-2 flex-shrink-0"
          >
            {actions}
          </div>
        )}
      </div>

      {/* Status bar */}
      {statusBar && (
        <div
          data-testid="page-statusbar"
          className="mb-4 flex items-center gap-3 px-3 py-2 rounded-md bg-muted text-xs text-muted-foreground font-mono overflow-x-auto"
        >
          {statusBar}
        </div>
      )}

      {/* Main content */}
      <div data-testid="page-content" className="flex-1">
        {children}
      </div>
    </div>
  );
}

export default PageShell;
