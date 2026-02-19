/**
 * ProgressBanner.tsx (v4.77.0 - Wave 33)
 *
 * Multi-step progress banner used during plan/run/export/simulate operations.
 * Replaces ad-hoc spinners. Shows deterministic step names.
 *
 * data-testids:
 *   progress-banner, progress-banner-step-{i}, progress-banner-complete,
 *   progress-banner-error
 */
import { cn } from "@/lib/utils";
import { CheckCircle2, Circle, Loader2, AlertCircle } from "lucide-react";

export interface ProgressStep {
  id: string;
  label: string;
  status: "pending" | "running" | "done" | "error";
}

interface ProgressBannerProps {
  steps: ProgressStep[];
  title?: string;
  className?: string;
}

export function ProgressBanner({ steps, title, className }: ProgressBannerProps) {
  const hasError = steps.some(s => s.status === "error");
  const allDone = steps.length > 0 && steps.every(s => s.status === "done");

  return (
    <div
      data-testid="progress-banner"
      className={cn(
        "rounded-md border px-4 py-3 text-sm",
        hasError
          ? "border-destructive/30 bg-destructive/5"
          : allDone
            ? "border-green-200 bg-green-50"
            : "border-blue-200 bg-blue-50",
        className
      )}
    >
      {title && (
        <p className="font-semibold mb-2 text-xs uppercase tracking-wide text-muted-foreground">
          {title}
        </p>
      )}
      <div className="flex flex-col gap-1.5">
        {steps.map((step, i) => (
          <div
            key={step.id}
            data-testid={`progress-banner-step-${i}`}
            className="flex items-center gap-2"
          >
            {step.status === "done" && (
              <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
            )}
            {step.status === "running" && (
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin flex-shrink-0" />
            )}
            {step.status === "pending" && (
              <Circle className="h-4 w-4 text-muted-foreground/40 flex-shrink-0" />
            )}
            {step.status === "error" && (
              <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0" />
            )}
            <span
              className={cn(
                step.status === "done"
                  ? "text-green-800"
                  : step.status === "error"
                    ? "text-destructive"
                    : step.status === "running"
                      ? "text-blue-800 font-medium"
                      : "text-muted-foreground"
              )}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>
      {allDone && (
        <p
          data-testid="progress-banner-complete"
          className="mt-2 text-xs font-medium text-green-700"
        >
          All steps complete
        </p>
      )}
      {hasError && (
        <p
          data-testid="progress-banner-error"
          className="mt-2 text-xs font-medium text-destructive"
        >
          One or more steps failed
        </p>
      )}
    </div>
  );
}

export default ProgressBanner;
