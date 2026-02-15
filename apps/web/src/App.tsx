import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import Dashboard from '@/pages/Dashboard';
import Portfolio from '@/pages/Portfolio';
import Scenarios from '@/pages/Scenarios';
import Agent from '@/pages/Agent';
import Reports from '@/pages/Reports';
import Settings from '@/pages/Settings';
// Phase 2A Pages (v1.1-v1.3)
import PortfolioLibrary from '@/pages/PortfolioLibrary';
import RunHistory from '@/pages/RunHistory';
import ComparePage from '@/pages/ComparePage';
import ReportsHubPage from '@/pages/ReportsHubPage';
import HedgeStudio from '@/pages/HedgeStudio';
// Phase 2B Pages (v1.4-v1.6)
import WorkspacesPage from '@/pages/WorkspacesPage';
import AuditPage from '@/pages/AuditPage';
import DevOpsPage from '@/pages/DevOpsPage';
import MonitoringPage from '@/pages/MonitoringPage';
import { AppProvider } from '@/lib/context';

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <AppLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/scenarios" element={<Scenarios />} />
            <Route path="/agent" element={<Agent />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
            {/* Phase 2A Routes */}
            <Route path="/library" element={<PortfolioLibrary />} />
            <Route path="/history" element={<RunHistory />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/reports-hub" element={<ReportsHubPage />} />
            <Route path="/hedge" element={<HedgeStudio />} />
            {/* Phase 2B Routes */}
            <Route path="/workspaces" element={<WorkspacesPage />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/devops" element={<DevOpsPage />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
          </Routes>
        </AppLayout>
      </AppProvider>
    </BrowserRouter>
  );
}
