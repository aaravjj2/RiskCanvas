/**
 * RightDrawer.tsx (v4.76.0 - Wave 33)
 *
 * Standard right-side drawer / panel used for diffs, previews, trace views.
 * - ESC closes
 * - Focus trap (first focusable element gets focus on open)
 * - Consistent 480px width
 *
 * data-testids: right-drawer, right-drawer-close, right-drawer-title
 */
import { useEffect, useRef, useCallback } from "react";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";
import { X } from "lucide-react";

interface RightDrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  headerActions?: ReactNode;
  children: ReactNode;
  width?: string;
  "data-testid"?: string;
}

export function RightDrawer({
  open,
  onClose,
  title,
  headerActions,
  children,
  width = "w-[480px]",
  "data-testid": testId = "right-drawer",
}: RightDrawerProps) {
  const closeRef = useRef<HTMLButtonElement>(null);

  // ESC key handler
  const handleKey = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onClose();
      }
    },
    [open, onClose]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [handleKey]);

  // Focus the close button when drawer opens
  useEffect(() => {
    if (open) {
      setTimeout(() => closeRef.current?.focus(), 50);
    }
  }, [open]);

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        data-testid="right-drawer-backdrop"
        className="fixed inset-0 bg-black/30 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="right-drawer-title-id"
        data-testid={testId}
        className={cn(
          "fixed right-0 top-0 h-full bg-background border-l border-border shadow-xl z-50 flex flex-col",
          width
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
          <h2
            id="right-drawer-title-id"
            data-testid="right-drawer-title"
            className="text-base font-semibold"
          >
            {title}
          </h2>
          <div className="flex items-center gap-2">
            {headerActions}
            <button
              ref={closeRef}
              data-testid="right-drawer-close"
              onClick={onClose}
              aria-label="Close drawer"
              className="p-1.5 rounded-md hover:bg-accent transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
      </div>
    </>
  );
}

export default RightDrawer;
