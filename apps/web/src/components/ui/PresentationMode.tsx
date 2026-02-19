/**
 * PresentationMode.tsx (v4.82.0 - Wave 35)
 *
 * Presentation Mode: guided demo rails for hackathon judging.
 * Three rails: GitLab, Microsoft, DigitalOcean.
 *
 * Context provides:
 *   - enabled / toggle()
 *   - current rail + step
 *   - next() / reset()
 *
 * data-testids (rendered in sidebar + steps):
 *   presentation-toggle, presentation-step-card,
 *   presentation-next-btn, presentation-step-title, presentation-progress,
 *   presentation-rail-select-{id}
 */
import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";

export interface PresentationStep {
  id: string;
  label: string;
  description: string;
  /** react-router path to navigate to */
  navigateTo?: string;
  /** data-testid of element to highlight */
  highlightTestId?: string;
}

export interface PresentationRail {
  id: string;
  name: string;
  steps: PresentationStep[];
}

/** GitLab hackathon story: MR Review → Policy V2 → Readiness → Pack */
export const RAIL_GITLAB: PresentationRail = {
  id: "gitlab",
  name: "GitLab Story",
  steps: [
    { id: "gl-1", label: "Open MR Review", description: "Navigate to Agentic MR Review", navigateTo: "/mr-review", highlightTestId: "nav-mr-review" },
    { id: "gl-2", label: "Plan MR Review", description: "Select a fixture MR and plan review", navigateTo: "/mr-review", highlightTestId: "mr-plan-btn" },
    { id: "gl-3", label: "Open Policy V2", description: "Navigate to Policy Registry V2", navigateTo: "/policies-v2", highlightTestId: "nav-policies-v2" },
    { id: "gl-4", label: "Create Policy", description: "Create a new policy version", navigateTo: "/policies-v2", highlightTestId: "pv2-create-btn" },
    { id: "gl-5", label: "Release Readiness", description: "Evaluate readiness gates", navigateTo: "/readiness", highlightTestId: "nav-readiness" },
    { id: "gl-6", label: "Export Pack", description: "Generate export pack and verify hash", navigateTo: "/exports", highlightTestId: "exports-page" },
  ],
};

/** Microsoft hackathon story: Agents → SRE Drill → Readiness → Export */
export const RAIL_MICROSOFT: PresentationRail = {
  id: "microsoft",
  name: "Microsoft Story",
  steps: [
    { id: "ms-1", label: "Open MR Review Agents", description: "Navigate to MR Review agent pipeline", navigateTo: "/mr-review", highlightTestId: "nav-mr-review" },
    { id: "ms-2", label: "Run Agent Pipeline", description: "Execute multi-agent code review", navigateTo: "/mr-review", highlightTestId: "mr-run-btn" },
    { id: "ms-3", label: "SRE Incident Drills", description: "Run incident response drill", navigateTo: "/incidents", highlightTestId: "nav-incidents" },
    { id: "ms-4", label: "Release Readiness", description: "Score 8-gate release readiness", navigateTo: "/readiness", highlightTestId: "readiness-evaluate-btn" },
    { id: "ms-5", label: "Exports Hub", description: "Review export packs with hash proofs", navigateTo: "/exports", highlightTestId: "exports-page" },
  ],
};

/** DigitalOcean hackathon story: Deploy readiness + Ops */
export const RAIL_DIGITALOCEAN: PresentationRail = {
  id: "digitalocean",
  name: "DigitalOcean Story",
  steps: [
    { id: "do-1", label: "Platform Health", description: "Check platform monitoring", navigateTo: "/platform", highlightTestId: "nav-platform" },
    { id: "do-2", label: "Ops Incident Drills", description: "Run ops incident runbook", navigateTo: "/incidents", highlightTestId: "nav-incidents" },
    { id: "do-3", label: "Readiness Gates", description: "Verify deploy readiness scores", navigateTo: "/readiness", highlightTestId: "nav-readiness" },
    { id: "do-4", label: "Workbench View", description: "All-in-one workbench experience", navigateTo: "/workbench", highlightTestId: "workbench-page" },
    { id: "do-5", label: "Export Artifacts", description: "Export and archive proof packs", navigateTo: "/exports", highlightTestId: "exports-list-ready" },
  ],
};

export const ALL_RAILS: PresentationRail[] = [RAIL_GITLAB, RAIL_MICROSOFT, RAIL_DIGITALOCEAN];

interface PresentationContextValue {
  enabled: boolean;
  toggle: () => void;
  rail: PresentationRail;
  setRailId: (id: string) => void;
  stepIndex: number;
  currentStep: PresentationStep | null;
  next: () => void;
  reset: () => void;
  totalSteps: number;
}

const PresentationContext = createContext<PresentationContextValue | undefined>(
  undefined
);

export function PresentationProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(false);
  const [railId, setRailId] = useState("gitlab");
  const [stepIndex, setStepIndex] = useState(0);
  const navigate = useNavigate();

  const rail = ALL_RAILS.find(r => r.id === railId) ?? RAIL_GITLAB;
  const currentStep = enabled ? (rail.steps[stepIndex] ?? null) : null;

  const toggle = useCallback(() => {
    setEnabled(v => !v);
    setStepIndex(0);
  }, []);

  const next = useCallback(() => {
    const step = rail.steps[stepIndex];
    if (step?.navigateTo) {
      navigate(step.navigateTo);
    }
    setStepIndex(prev => Math.min(prev + 1, rail.steps.length - 1));
  }, [stepIndex, rail, navigate]);

  const reset = useCallback(() => {
    setStepIndex(0);
  }, []);

  const handleSetRailId = useCallback((id: string) => {
    setRailId(id);
    setStepIndex(0);
  }, []);

  return (
    <PresentationContext.Provider
      value={{
        enabled,
        toggle,
        rail,
        setRailId: handleSetRailId,
        stepIndex,
        currentStep,
        next,
        reset,
        totalSteps: rail.steps.length,
      }}
    >
      {children}
    </PresentationContext.Provider>
  );
}

export function usePresentationMode() {
  const ctx = useContext(PresentationContext);
  if (!ctx) throw new Error("usePresentationMode must be inside PresentationProvider");
  return ctx;
}

/** Floating step card shown when presentation mode is active */
export function PresentationStepCard() {
  const { enabled, currentStep, stepIndex, totalSteps, next, reset, toggle } =
    usePresentationMode();

  if (!enabled || !currentStep) return null;

  return (
    <div
      data-testid="presentation-step-card"
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[90] bg-background border border-border rounded-xl shadow-xl px-5 py-4 min-w-[340px] max-w-md"
    >
      <div className="flex items-center justify-between mb-2">
        <p
          data-testid="presentation-progress"
          className="text-xs text-muted-foreground font-mono"
        >
          Step {stepIndex + 1} / {totalSteps}
        </p>
        <button
          onClick={toggle}
          className="text-xs text-muted-foreground hover:text-foreground"
          data-testid="presentation-exit"
        >
          Exit
        </button>
      </div>
      <p
        data-testid="presentation-step-title"
        className="text-sm font-semibold mb-1"
      >
        {currentStep.label}
      </p>
      <p className="text-xs text-muted-foreground mb-3">
        {currentStep.description}
      </p>
      <div className="flex items-center gap-2">
        <button
          data-testid="presentation-next-btn"
          onClick={next}
          disabled={stepIndex >= totalSteps - 1}
          className="flex-1 px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md disabled:opacity-40"
        >
          {stepIndex >= totalSteps - 1 ? "Complete" : "Next Step →"}
        </button>
        <button
          data-testid="presentation-reset-btn"
          onClick={reset}
          className="px-3 py-1.5 text-xs border border-border rounded-md hover:bg-muted"
        >
          ↺
        </button>
      </div>
    </div>
  );
}
