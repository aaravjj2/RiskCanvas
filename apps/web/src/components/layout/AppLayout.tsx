import { Link, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, 
  Briefcase, 
  Zap, 
  Bot, 
  FileText, 
  Settings as SettingsIcon 
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { path: "/", icon: LayoutDashboard, label: "Dashboard" },
  { path: "/portfolio", icon: Briefcase, label: "Portfolio" },
  { path: "/scenarios", icon: Zap, label: "Scenarios" },
  { path: "/agent", icon: Bot, label: "Agent" },
  { path: "/reports", icon: FileText, label: "Reports" },
  { path: "/settings", icon: SettingsIcon, label: "Settings" },
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
            <p className="text-xs text-muted-foreground mt-1">v1.0.0</p>
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
                      data-testid={`nav-${item.label.toLowerCase()}`}
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
    </div>
  );
}

export default AppLayout;
