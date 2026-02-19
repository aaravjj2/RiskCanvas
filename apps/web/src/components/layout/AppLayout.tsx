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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { CommandPalette } from "@/components/CommandPalette";
import { usePresentationMode, ALL_RAILS, PresentationStepCard } from "@/components/ui/PresentationMode";
import TenantSwitcher from "@/components/ui/TenantSwitcher";

const navItems = [
  { path: "/", icon: LayoutDashboard, label: "Dashboard", testid: "dashboard" },
  { path: "/portfolio", icon: Briefcase, label: "Portfolio", testid: "portfolio" },
  { path: "/scenarios", icon: Zap, label: "Scenarios", testid: "scenarios" },
  { path: "/agent", icon: Bot, label: "Agent", testid: "agent" },
  { path: "/reports", icon: FileText, label: "Reports", testid: "reports" },
  { path: "/history", icon: History, label: "Run History", testid: "history" },
  { path: "/library", icon: Library, label: "Library", testid: "library" },
  { path: "/jobs", icon: Jobs, label: "Jobs", testid: "jobs" },
  { path: "/devops", icon: Wrench, label: "DevOps", testid: "devops" },
  { path: "/platform", icon: Activity, label: "Platform", testid: "platform" },
  { path: "/rates", icon: TrendingUp, label: "Rates", testid: "rates" },
  { path: "/stress", icon: FlameKindling, label: "Stress", testid: "stress" },
  { path: "/governance", icon: ShieldCheck, label: "Governance", testid: "governance" },
  { path: "/sre", icon: ShieldCheck, label: "SRE Playbooks", testid: "sre" },
  { path: "/activity", icon: Radio, label: "Activity", testid: "activity" },
  { path: "/search", icon: Search, label: "Search", testid: "search" },
  { path: "/settings", icon: SettingsIcon, label: "Settings", testid: "settings" },
  { path: "/market", icon: BarChart2, label: "Market Data", testid: "market" },
  // Wave 15
  { path: "/pnl", icon: LineChart, label: "PnL Attribution", testid: "pnl" },
  // Wave 16
  { path: "/scenarios-dsl", icon: Code2, label: "Scenario DSL", testid: "scenarios-dsl" },
  // Wave 17
  { path: "/replay", icon: RefreshCw, label: "Replay", testid: "replay" },
  // Wave 18
  { path: "/construction", icon: Building2, label: "Construction", testid: "construction" },
  // Wave 19
  { path: "/fx", icon: DollarSign, label: "FX Risk", testid: "fx" },
  // Wave 20
  { path: "/credit", icon: CreditCard, label: "Credit Risk", testid: "credit" },
  // Wave 21
  { path: "/liquidity", icon: Droplets, label: "Liquidity", testid: "liquidity" },
  // Wave 22
  { path: "/approvals", icon: ClipboardCheck, label: "Approvals", testid: "approvals" },
  // Wave 23
  { path: "/gitlab", icon: GitMerge, label: "GitLab MR", testid: "gitlab" },
  // Wave 24
  { path: "/ci", icon: Cpu, label: "CI Intel", testid: "ci" },
  // Wave 25
  { path: "/security", icon: Lock, label: "Security", testid: "security" },
  // Wave 26
  { path: "/mr-review", icon: FileDiff, label: "MR Review", testid: "mr-review" },
  // Wave 27
  { path: "/incidents", icon: AlertTriangle, label: "Incident Drills", testid: "incidents" },
  // Wave 28
  { path: "/readiness", icon: Rocket, label: "Readiness", testid: "readiness" },
  // Wave 29
  { path: "/workflows", icon: GitBranch, label: "Workflows", testid: "workflows" },
  // Wave 30
  { path: "/policies-v2", icon: BookOpen, label: "Policies V2", testid: "policies-v2" },
  // Wave 31
  { path: "/search-v2", icon: Database, label: "Search V2", testid: "search-v2" },
  // Wave 32
  { path: "/judge-mode", icon: Scale, label: "Judge Mode", testid: "judge-mode" },
  // Wave 34
  { path: "/exports", icon: Package, label: "Exports Hub", testid: "exports" },
  // Wave 37
  { path: "/workbench", icon: MonitorPlay, label: "Workbench", testid: "workbench" },
  // Wave 41-48: Enterprise Layer
  { path: "/admin", icon: Users, label: "Admin", testid: "admin" },
  { path: "/artifacts", icon: Archive, label: "Artifacts", testid: "artifacts" },
  { path: "/attestations", icon: Link2, label: "Attestations", testid: "attestations" },
  { path: "/compliance", icon: ClipboardCheck, label: "Compliance", testid: "compliance" },
  // Wave 49-56: Dataset & Scenario & Review Layer
  { path: "/datasets", icon: Database, label: "Datasets", testid: "datasets" },
  { path: "/scenario-composer", icon: Layers, label: "Scenario Composer", testid: "scenario-composer" },
  { path: "/reviews", icon: FileCheck2, label: "Reviews", testid: "reviews" },
];

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
            <p className="text-xs text-muted-foreground mt-1" data-testid="version-badge">v5.45.0</p>
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
      <main className="flex-1 overflow-auto">
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
