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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { CommandPalette } from "@/components/CommandPalette";

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
];

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
            <p className="text-xs text-muted-foreground mt-1" data-testid="version-badge">v4.25.0</p>
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
          <div className="p-4 border-t border-border text-xs text-muted-foreground">
            <p>Engine v0.1.0</p>
            <p className="mt-1">DEMO Mode</p>
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
    </div>
  );
}

export default AppLayout;
