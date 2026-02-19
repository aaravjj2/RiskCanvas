/**
 * LoadingSkeleton.tsx (v4.74.0 - Wave 33)
 *
 * Deterministic loading skeleton used while async data is in flight.
 * data-testid: loading-skeleton
 */
import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  rows?: number;
  className?: string;
}

function SkeletonBar({ width }: { width: string }) {
  return (
    <div
      className={cn(
        "h-4 rounded bg-muted animate-pulse",
        width
      )}
    />
  );
}

export function LoadingSkeleton({ rows = 4, className }: LoadingSkeletonProps) {
  const widths = ["w-full", "w-5/6", "w-4/5", "w-11/12", "w-3/4", "w-full"];
  return (
    <div
      data-testid="loading-skeleton"
      className={cn("flex flex-col gap-3 py-4", className)}
    >
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonBar key={i} width={widths[i % widths.length]} />
      ))}
    </div>
  );
}

export default LoadingSkeleton;
