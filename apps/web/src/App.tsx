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
// Phase 2C Pages (v1.7-v1.9)
import GovernancePage from '@/pages/GovernancePage';
import BondsPage from '@/pages/BondsPage';
// Phase 3 Pages (v2.0-v2.2)
import MicrosoftModePage from '@/pages/MicrosoftModePage';
// Phase 4 Pages (v2.3-v2.5)
import JobsPage from '@/pages/JobsPage';
// Wave 6 Pages (v2.9-v3.2)
import PlatformPage from '@/pages/PlatformPage';
// Wave 7+8 Pages (v3.3-v3.6)
import RatesPage from '@/pages/RatesPage';
import StressPage from '@/pages/StressPage';
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
            {/* Phase 2C Routes */}
            <Route path="/governance" element={<GovernancePage />} />
            <Route path="/bonds" element={<BondsPage />} />
            {/* Phase 3 Routes */}
            <Route path="/microsoft" element={<MicrosoftModePage />} />
            {/* Phase 4 Routes */}
            <Route path="/jobs" element={<JobsPage />} />
            {/* Wave 6 Routes */}
            <Route path="/platform" element={<PlatformPage />} />
            {/* Wave 7+8 Routes */}
            <Route path="/rates" element={<RatesPage />} />
            <Route path="/stress" element={<StressPage />} />
          </Routes>
        </AppLayout>
      </AppProvider>
    </BrowserRouter>
  );
}
