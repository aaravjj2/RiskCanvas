/**
 * featureFlags.ts — Surface-area control for RiskCanvas
 *
 * Default "SAFE" set: only the 3 core judge flows + harness are visible in nav.
 * All routes remain accessible via direct URL at all times.
 *
 * Override in localStorage with key RC_FLAGS:
 *   localStorage.setItem('RC_FLAGS', JSON.stringify({ scenario_composer: false }))
 *
 * v5.53.1
 */

/** Canonical flag names */
export type FeatureFlag =
  | "dashboard"
  | "datasets"
  | "scenario_composer"
  | "reviews"
  | "exports"
  | "harness"
  | "rooms"
  | "devops"
  | "microsoft"
  | "evals"
  | "evidence"
  | "runbooks";

/**
 * Default SAFE flags — minimum surface for 3 core judge flows.
 * Everything else defaults to false and is hidden from nav.
 */
const DEFAULT_FLAGS: Record<string, boolean> = {
  dashboard: true,
  datasets: true,           // Flow A: Dataset loop
  scenario_composer: true,  // Flow B: Scenario loop
  reviews: true,            // Flow C: Approval/export loop
  exports: true,            // Flow C: Export dependency
  harness: true,            // /__harness — System Checks
  rooms: true,              // Depth Wave: Decision Rooms (home UX)
  devops: true,             // Depth Wave: DevOps + offline MR review
  microsoft: true,          // Depth Wave: MCP v2 Microsoft mode
  evals: true,              // Depth Wave: Eval harness v3
  evidence: true,            // Wave 65-72: Evidence Graph
  runbooks: true,            // Wave 65-72: Runbooks
};

/** Returns true if the given feature flag is enabled */
export function isEnabled(flag: string): boolean {
  try {
    const override = localStorage.getItem("RC_FLAGS");
    if (override) {
      const parsed = JSON.parse(override) as Record<string, boolean>;
      if (flag in parsed) return Boolean(parsed[flag]);
    }
  } catch {
    // localStorage unavailable (SSR / sandboxed context) — use defaults
  }
  return DEFAULT_FLAGS[flag] ?? false;
}

/** Returns a merged snapshot of all flags (defaults + localStorage overrides) */
export function getAllFlags(): Record<string, boolean> {
  const flags: Record<string, boolean> = { ...DEFAULT_FLAGS };
  try {
    const override = localStorage.getItem("RC_FLAGS");
    if (override) {
      const parsed = JSON.parse(override) as Record<string, boolean>;
      Object.assign(flags, parsed);
    }
  } catch {}
  return flags;
}

/** Convenience: returns a sorted list of [flag, enabled] pairs for display */
export function listFlags(): Array<{ flag: string; enabled: boolean }> {
  const all = getAllFlags();
  return Object.entries(all)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([flag, enabled]) => ({ flag, enabled }));
}
