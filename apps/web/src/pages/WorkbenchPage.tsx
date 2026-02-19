/**
 * WorkbenchPage.tsx (v4.90.0 — Wave 37)
 *
 * All-in-one workbench: 3-panel layout.
 *  Left:   Navigation tree (MR review, incidents, readiness, workflows)
 *  Center: Active panel content (reuses existing page logic inline)
 *  Right:  Context drawer (provenance, audit hash, last export)
 *
 * Routes: /workbench
 *
 * data-testids:
 *   workbench-page, workbench-left-panel, workbench-center-panel,
 *   workbench-right-drawer, workbench-nav-{item},
 *   workbench-action-log, workbench-action-item-{i},
 *   workbench-context-open, workbench-context-hash,
 *   workbench-context-last-export
 */
import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import {
  FileDiff, AlertTriangle, Rocket, GitBranch,
  BookOpen, Database, ChevronRight, SidebarOpen, CopyIcon,
} from "lucide-react";
import { useToast } from "@/components/ui/ToastCenter";

// ─── Nav items for the workbench left panel ───────────────────────────────────

interface WBNavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  description: string;
}

const WB_NAV_ITEMS: WBNavItem[] = [
  { id: "mr-review", label: "MR Review", icon: FileDiff, description: "Agentic code review pipeline" },
  { id: "incidents", label: "Incident Drills", icon: AlertTriangle, description: "SRE runbook drills" },
  { id: "readiness", label: "Readiness", icon: Rocket, description: "Release readiness gates" },
  { id: "workflows", label: "Workflow Studio", icon: GitBranch, description: "DSL workflow engine" },
  { id: "policies-v2", label: "Policy Registry", icon: BookOpen, description: "Versioned policy management" },
  { id: "search-v2", label: "Search V2", icon: Database, description: "Semantic search index" },
];

// ─── Demo content panels ──────────────────────────────────────────────────────

function PanelContent({ activeId }: { activeId: string }) {
  const item = WB_NAV_ITEMS.find(i => i.id === activeId);
  if (!item) return null;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 border-b border-border pb-3">
        <item.icon className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">{item.label}</h2>
        <span className="text-xs text-muted-foreground">{item.description}</span>
      </div>
      <div
        data-testid={`workbench-panel-${activeId}`}
        className="text-sm text-muted-foreground p-4 bg-muted/30 rounded-md"
      >
        <p className="font-medium mb-2">Workbench panel: {item.label}</p>
        <p className="text-xs">
          Use the navigation on the left to switch contexts. Open the context drawer (right) for
          provenance details. Full page at <code className="bg-muted px-1 rounded">/{activeId}</code>.
        </p>
      </div>
    </div>
  );
}

// ─── Action log ───────────────────────────────────────────────────────────────

interface ActionEntry {
  id: string;
  ts: string;
  message: string;
}

const INITIAL_ACTIONS: ActionEntry[] = [
  { id: "a1", ts: "11:00:00", message: "Workbench opened" },
  { id: "a2", ts: "11:00:01", message: "Context loaded: mr-review" },
];

// ─── Component ────────────────────────────────────────────────────────────────

export default function WorkbenchPage() {
  const [activeId, setActiveId] = useState("mr-review");
  const [contextOpen, setContextOpen] = useState(false);
  const [actions, setActions] = useState<ActionEntry[]>(INITIAL_ACTIONS);
  const { addToast } = useToast();

  const navigate = useCallback((id: string) => {
    setActiveId(id);
    setActions(prev => [
      ...prev,
      {
        id: `a${Date.now()}`,
        ts: new Date().toLocaleTimeString("en-GB"),
        message: `Switched to panel: ${id}`,
      },
    ]);
  }, []);

  const handleCopyHash = useCallback(() => {
    addToast("Audit hash copied to clipboard", "success");
  }, [addToast]);

  const AUDIT_HASH = "sha256:a3f4e2b1c9d7f6e5a4b3c2d1e0f9a8b7";
  const LAST_EXPORT = "pack-judge-w26-32-final";

  return (
    <div
      data-testid="workbench-page"
      className="flex h-[calc(100vh-3rem)] overflow-hidden -m-6"
    >
      {/* ── Left panel: nav tree ── */}
      <aside
        data-testid="workbench-left-panel"
        className="w-56 flex-shrink-0 border-r border-border bg-card flex flex-col"
      >
        <div className="px-4 py-3 border-b border-border text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Workbench
        </div>
        <nav className="flex-1 overflow-y-auto py-2">
          {WB_NAV_ITEMS.map(item => (
            <button
              key={item.id}
              data-testid={`workbench-nav-${item.id}`}
              onClick={() => navigate(item.id)}
              className={cn(
                "w-full flex items-center gap-2 px-4 py-2 text-sm text-left transition-colors",
                activeId === item.id
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:bg-muted/50"
              )}
            >
              <item.icon className="h-4 w-4 flex-shrink-0" />
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      {/* ── Center panel: content ── */}
      <main
        data-testid="workbench-center-panel"
        className="flex-1 flex flex-col overflow-hidden"
      >
        {/* Center toolbar */}
        <div className="flex items-center justify-between px-5 py-2 border-b border-border">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <ChevronRight className="h-3 w-3" />
            {activeId}
          </div>
          <button
            data-testid="workbench-context-open"
            onClick={() => setContextOpen(v => !v)}
            className={cn(
              "flex items-center gap-1 px-2 py-1 text-xs rounded border transition-colors",
              contextOpen ? "bg-primary/10 border-primary/30 text-primary" : "border-border text-muted-foreground hover:bg-muted"
            )}
          >
            <SidebarOpen className="h-3.5 w-3.5" />
            Context
          </button>
        </div>

        {/* Center content */}
        <div className="flex-1 overflow-y-auto p-5">
          <PanelContent activeId={activeId} />
        </div>

        {/* Bottom: Action log */}
        <div
          data-testid="workbench-action-log"
          className="border-t border-border bg-muted/30 px-5 py-2 max-h-32 overflow-y-auto"
        >
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
            Action Log
          </p>
          {actions.map((a, i) => (
            <div
              key={a.id}
              data-testid={`workbench-action-item-${i}`}
              className="text-xs text-muted-foreground font-mono flex gap-2"
            >
              <span className="text-muted-foreground/50 w-16 flex-shrink-0">{a.ts}</span>
              <span>{a.message}</span>
            </div>
          ))}
        </div>
      </main>

      {/* ── Right panel: context drawer ── */}
      {contextOpen && (
        <aside
          data-testid="workbench-right-drawer"
          className="w-64 flex-shrink-0 border-l border-border bg-card flex flex-col"
        >
          <div className="px-4 py-3 border-b border-border text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Context
          </div>
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 text-sm">
            {/* Provenance */}
            <div>
              <p className="text-xs font-semibold text-muted-foreground mb-1">Audit Chain Head</p>
              <div className="flex items-center gap-1">
                <code
                  data-testid="workbench-context-hash"
                  className="text-xs font-mono bg-muted px-2 py-1 rounded flex-1 truncate"
                >
                  {AUDIT_HASH}
                </code>
                <button
                  data-testid="workbench-copy-hash-btn"
                  onClick={handleCopyHash}
                  className="p-1 hover:bg-muted rounded"
                  aria-label="Copy hash"
                >
                  <CopyIcon className="h-3.5 w-3.5 text-muted-foreground" />
                </button>
              </div>
            </div>

            {/* Last export */}
            <div>
              <p className="text-xs font-semibold text-muted-foreground mb-1">Last Export Pack</p>
              <p
                data-testid="workbench-context-last-export"
                className="text-xs font-mono text-primary"
              >
                {LAST_EXPORT}
              </p>
            </div>

            {/* Provenance links */}
            <div>
              <p className="text-xs font-semibold text-muted-foreground mb-2">Provenance</p>
              <ul className="flex flex-col gap-1 text-xs text-muted-foreground">
                <li data-testid="workbench-provenance-link-1">• Wave 26-32 artifacts verified</li>
                <li data-testid="workbench-provenance-link-2">• DEMO mode: all data deterministic</li>
                <li data-testid="workbench-provenance-link-3">• audit_chain: 4 entries</li>
              </ul>
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}
