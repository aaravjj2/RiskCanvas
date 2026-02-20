import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Briefcase,
  Zap,
  Bot,
  FileText,
  Settings as SettingsIcon,
  History,
  Library,
  Briefcase as Jobs,
  Wrench,
  Activity,
  TrendingUp,
  FlameKindling,
  ShieldCheck,
  Search,
  Radio,
  BarChart2,
  LineChart,
  Code2,
  RefreshCw,
  Building2,
  DollarSign,
  CreditCard,
  Droplets,
  ClipboardCheck,
  GitMerge,
  Cpu,
  Lock,
  FileDiff,
  AlertTriangle,
  Rocket,
  GitBranch,
  BookOpen,
  Database,
  Scale,
  Package,
  MonitorPlay,
  Presentation,
  Users,
  Archive,
  Link2,
  Layers,
  FileCheck2,
  GitGraph,
  DoorOpen,
  PlayCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { CommandPalette } from "@/components/CommandPalette";
import { usePresentationMode, ALL_RAILS, PresentationStepCard } from "@/components/ui/PresentationMode";
import TenantSwitcher from "@/components/ui/TenantSwitcher";
import EvidenceBar from "@/components/ui/EvidenceBar";
import { isEnabled } from "@/lib/featureFlags";

/**
 * ALL_NAV_ITEMS — each item carries a `flag` key.
 * Items are shown in the sidebar only when isEnabled(flag) is true.
 * Default safe flags: dashboard, datasets, scenario_composer, reviews, exports, harness.
 * All routes remain accessible via direct URL regardless of flag state.
 * v5.53.1
 */
const ALL_NAV_ITEMS = [
  // ── Always-visible core ──────────────────────────────────────────────────
  { path: "/", icon: LayoutDashboard, label: "Dashboard", testid: "dashboard", flag: "dashboard" },
  // ── Flow A: Dataset loop ──────────────────────────────────────────────────
  { path: "/datasets", icon: Database, label: "Datasets", testid: "datasets", flag: "datasets" },
  // ── Flow B: Scenario loop ─────────────────────────────────────────────────
  { path: "/scenario-composer", icon: Layers, label: "Scenario Composer", testid: "scenario-composer", flag: "scenario_composer" },
  // ── Flow C: Approval / Export loop ───────────────────────────────────────
  { path: "/reviews", icon: FileCheck2, label: "Reviews", testid: "reviews", flag: "reviews" },
  { path: "/exports", icon: Package, label: "Exports Hub", testid: "exports", flag: "exports" },
  // ── Behind feature flags (not shown by default) ───────────────────────────
  { path: "/portfolio", icon: Briefcase, label: "Portfolio", testid: "portfolio", flag: "portfolio" },
  { path: "/scenarios", icon: Zap, label: "Scenarios", testid: "scenarios", flag: "scenarios_legacy" },
  { path: "/agent", icon: Bot, label: "Agent", testid: "agent", flag: "agent" },
  { path: "/reports", icon: FileText, label: "Reports", testid: "reports", flag: "reports" },
  { path: "/history", icon: History, label: "Run History", testid: "history", flag: "run_history" },
  { path: "/library", icon: Library, label: "Library", testid: "library", flag: "library" },
  { path: "/jobs", icon: Jobs, label: "Jobs", testid: "jobs", flag: "jobs" },
  { path: "/devops", icon: Wrench, label: "DevOps", testid: "devops", flag: "devops" },
  { path: "/platform", icon: Activity, label: "Platform", testid: "platform", flag: "platform" },
  { path: "/rates", icon: TrendingUp, label: "Rates", testid: "rates", flag: "rates" },
  { path: "/stress", icon: FlameKindling, label: "Stress", testid: "stress", flag: "stress" },
  { path: "/governance", icon: ShieldCheck, label: "Governance", testid: "governance", flag: "governance" },
  { path: "/sre", icon: ShieldCheck, label: "SRE Playbooks", testid: "sre", flag: "sre" },
  { path: "/activity", icon: Radio, label: "Activity", testid: "activity", flag: "activity" },
  { path: "/search", icon: Search, label: "Search", testid: "search", flag: "search" },
  { path: "/settings", icon: SettingsIcon, label: "Settings", testid: "settings", flag: "settings" },
  { path: "/market", icon: BarChart2, label: "Market Data", testid: "market", flag: "market" },
  { path: "/pnl", icon: LineChart, label: "PnL Attribution", testid: "pnl", flag: "pnl" },
  { path: "/scenarios-dsl", icon: Code2, label: "Scenario DSL", testid: "scenarios-dsl", flag: "scenarios_dsl" },
  { path: "/replay", icon: RefreshCw, label: "Replay", testid: "replay", flag: "replay" },
  { path: "/construction", icon: Building2, label: "Construction", testid: "construction", flag: "construction" },
  { path: "/fx", icon: DollarSign, label: "FX Risk", testid: "fx", flag: "fx" },
  { path: "/credit", icon: CreditCard, label: "Credit Risk", testid: "credit", flag: "credit" },
  { path: "/liquidity", icon: Droplets, label: "Liquidity", testid: "liquidity", flag: "liquidity" },
  { path: "/approvals", icon: ClipboardCheck, label: "Approvals", testid: "approvals", flag: "approvals" },
  { path: "/gitlab", icon: GitMerge, label: "GitLab MR", testid: "gitlab", flag: "gitlab" },
  { path: "/ci", icon: Cpu, label: "CI Intel", testid: "ci", flag: "ci" },
  { path: "/security", icon: Lock, label: "Security", testid: "security", flag: "security" },
  { path: "/mr-review", icon: FileDiff, label: "MR Review", testid: "mr-review", flag: "mr_review" },
  { path: "/incidents", icon: AlertTriangle, label: "Incident Drills", testid: "incidents", flag: "incidents" },
  { path: "/readiness", icon: Rocket, label: "Readiness", testid: "readiness", flag: "readiness" },
  { path: "/workflows", icon: GitBranch, label: "Workflows", testid: "workflows", flag: "workflows" },
  { path: "/policies-v2", icon: BookOpen, label: "Policies V2", testid: "policies-v2", flag: "policies_v2" },
  { path: "/search-v2", icon: Database, label: "Search V2", testid: "search-v2", flag: "search_v2" },
  { path: "/judge-mode", icon: Scale, label: "Judge Mode", testid: "judge-mode", flag: "judge_mode" },
  { path: "/workbench", icon: MonitorPlay, label: "Workbench", testid: "workbench", flag: "workbench" },
  { path: "/admin", icon: Users, label: "Admin", testid: "admin", flag: "admin" },
  { path: "/artifacts", icon: Archive, label: "Artifacts", testid: "artifacts", flag: "artifacts" },
  { path: "/attestations", icon: Link2, label: "Attestations", testid: "attestations", flag: "attestations" },
  { path: "/compliance", icon: ClipboardCheck, label: "Compliance", testid: "compliance", flag: "compliance" },
  { path: "/evidence", icon: GitGraph, label: "Evidence Graph", testid: "evidence", flag: "evidence" },
  { path: "/rooms", icon: DoorOpen, label: "Decision Rooms", testid: "rooms", flag: "rooms" },
  { path: "/runbooks", icon: PlayCircle, label: "Runbooks", testid: "runbooks", flag: "runbooks" },
  // ── Depth Wave (v5.56.1-v5.60.0) ────────────────────────────────────────
  { path: "/evals", icon: BarChart2, label: "Eval Harness v3", testid: "evals", flag: "evals" },
  { path: "/microsoft", icon: Cpu, label: "Microsoft Mode", testid: "microsoft", flag: "microsoft" },
];

// Only show items whose feature flag is enabled
const navItems = ALL_NAV_ITEMS.filter(item => isEnabled(item.flag));

function PresentationToggle() {
  const { enabled, toggle, rail, setRailId } = usePresentationMode();
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <button
          data-testid="presentation-toggle"
          onClick={toggle}
          aria-pressed={enabled}
          className={cn(
            "flex items-center gap-1.5 px-2 py-1 text-xs rounded border transition-colors w-full",
            enabled
              ? "bg-primary/10 border-primary/30 text-primary font-medium"
              : "border-border text-muted-foreground hover:bg-muted"
          )}
        >
          <Presentation className="h-3.5 w-3.5" />
          {enabled ? "Demo Rail ON" : "Demo Rail"}
        </button>
      </div>
      {enabled && (
        <div className="flex flex-col gap-1 pl-1">
          {ALL_RAILS.map(r => (
            <button
              key={r.id}
              data-testid={`presentation-rail-select-${r.id}`}
              onClick={() => setRailId(r.id)}
              className={cn(
                "text-xs px-2 py-0.5 rounded text-left transition-colors",
                rail.id === r.id ? "text-primary font-medium" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {rail.id === r.id ? "▶ " : "  "}{r.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-background" data-testid="app-layout">
      {/* Left sidebar */}
      <aside className="w-64 border-r border-border bg-card" data-testid="sidebar">
        <div className="flex flex-col h-full">
          {/* Logo/Brand */}
          <div className="p-6 border-b border-border">
            <h1 className="text-xl font-bold text-primary" data-testid="app-title">
              RiskCanvas
            </h1>
            <p className="text-xs text-muted-foreground mt-1" data-testid="version-badge">v5.61.0</p>
            <div className="mt-2">
              <TenantSwitcher />
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4" data-testid="nav">
            <ul className="space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      data-testid={`nav-${item.testid}`}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                        isActive
                          ? "bg-primary text-primary-foreground"
                          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-border text-xs text-muted-foreground flex flex-col gap-2">
            <PresentationToggle />
            <p>Engine v0.1.0</p>
            <p>DEMO Mode</p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto flex flex-col">
        <EvidenceBar />
        <div className="container mx-auto p-6" data-testid="main-content">
          {children}
        </div>
      </main>

      {/* Command Palette (Ctrl+K) */}
      <CommandPalette />

      {/* Presentation Mode floating step card */}
      <PresentationStepCard />
    </div>
  );
}

export default AppLayout;
