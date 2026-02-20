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
// Wave 9+10 Pages (v3.7-v4.0)
import SREPlaybooksPage from '@/pages/SREPlaybooksPage';
// Wave 11+12 Pages (v4.1-v4.4)
import ActivityPage from '@/pages/ActivityPage';
import SearchPage from '@/pages/SearchPage';
// v4.5.0 UI Test Harness
import TestHarnessPage from '@/pages/TestHarnessPage';
// Wave 13+14 Pages (v4.6-v4.9)
import MarketDataPage from '@/pages/MarketDataPage';
// Wave 15 Pages (v4.10-v4.13)
import PnLAttributionPage from '@/pages/PnLAttributionPage';
// Wave 16 Pages (v4.14-v4.17)
import ScenariosDSLPage from '@/pages/ScenariosDSLPage';
// Wave 17 Pages (v4.18-v4.21)
import ReplayPage from '@/pages/ReplayPage';
// Wave 18 Pages (v4.22-v4.25)
import ConstructionStudioPage from '@/pages/ConstructionStudioPage';
// Wave 19-25 Pages (v4.26-v4.49)
import FXPage from '@/pages/FXPage';
import CreditPage from '@/pages/CreditPage';
import LiquidityPage from '@/pages/LiquidityPage';
import ApprovalsPage from '@/pages/ApprovalsPage';
import GitLabPage from '@/pages/GitLabPage';
import CIPage from '@/pages/CIPage';
import SecurityPage from '@/pages/SecurityPage';
import MRReviewPage from '@/pages/MRReviewPage';
import IncidentDrillsPage from '@/pages/IncidentDrillsPage';
import ReleaseReadinessPage from '@/pages/ReleaseReadinessPage';
import WorkflowStudioPage from '@/pages/WorkflowStudioPage';
import PoliciesV2Page from '@/pages/PoliciesV2Page';
import SearchV2Page from '@/pages/SearchV2Page';
import JudgeModePage from '@/pages/JudgeModePage';
// Wave 33-40 Pages (v4.74-v4.97)
import ExportsHubPage from '@/pages/ExportsHubPage';
import WorkbenchPage from '@/pages/WorkbenchPage';
// Wave 41-48 Pages (v4.98-v5.21)
import AdminPage from '@/pages/AdminPage';
import ArtifactsPage from '@/pages/ArtifactsPage';
import AttestationsPage from '@/pages/AttestationsPage';
import CompliancePage from '@/pages/CompliancePage';
// Wave 49-56 Pages (v5.22-v5.45)
import DatasetsPage from '@/pages/DatasetsPage';
import ScenarioComposerPage from '@/pages/ScenarioComposerPage';
import ReviewsPage from '@/pages/ReviewsPage';
// Wave 65-67 Pages (v5.54.0-v5.56.0)
import EvidencePage from '@/pages/EvidencePage';
import RoomsPage from '@/pages/RoomsPage';
import RunbooksPage from '@/pages/RunbooksPage';
// Depth Wave (v5.56.1-v5.60.0)
import EvalsPage from '@/pages/EvalsPage';
import { AppProvider } from '@/lib/context';
import { ToastProvider } from '@/components/ui/ToastCenter';
import { PresentationProvider } from '@/components/ui/PresentationMode';

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <ToastProvider>
          <PresentationProvider>
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
            {/* Wave 9+10 Routes */}
            <Route path="/sre" element={<SREPlaybooksPage />} />
            {/* Wave 11+12 Routes */}
            <Route path="/activity" element={<ActivityPage />} />
            <Route path="/search" element={<SearchPage />} />
            {/* v4.5.0 UI Test Harness */}
            <Route path="/__harness" element={<TestHarnessPage />} />
            {/* Wave 13+14 Routes (v4.6-v4.9) */}
            <Route path="/market" element={<MarketDataPage />} />
            {/* Wave 15 Routes (v4.10-v4.13) */}
            <Route path="/pnl" element={<PnLAttributionPage />} />
            {/* Wave 16 Routes (v4.14-v4.17) */}
            <Route path="/scenarios-dsl" element={<ScenariosDSLPage />} />
            {/* Wave 17 Routes (v4.18-v4.21) */}
            <Route path="/replay" element={<ReplayPage />} />
            {/* Wave 18 Routes (v4.22-v4.25) */}
            <Route path="/construction" element={<ConstructionStudioPage />} />
            {/* Wave 19-25 Routes (v4.26-v4.49) */}
            <Route path="/fx" element={<FXPage />} />
            <Route path="/credit" element={<CreditPage />} />
            <Route path="/liquidity" element={<LiquidityPage />} />
            <Route path="/approvals" element={<ApprovalsPage />} />
            <Route path="/gitlab" element={<GitLabPage />} />
            <Route path="/ci" element={<CIPage />} />
            <Route path="/security" element={<SecurityPage />} />
            {/* Wave 26-32 Routes (v4.50-v4.73) */}
            <Route path="/mr-review" element={<MRReviewPage />} />
            <Route path="/incidents" element={<IncidentDrillsPage />} />
            <Route path="/readiness" element={<ReleaseReadinessPage />} />
            <Route path="/workflows" element={<WorkflowStudioPage />} />
            <Route path="/policies-v2" element={<PoliciesV2Page />} />
            <Route path="/search-v2" element={<SearchV2Page />} />
            <Route path="/judge-mode" element={<JudgeModePage />} />
            {/* Wave 33-40 Routes (v4.74-v4.97) */}
            <Route path="/exports" element={<ExportsHubPage />} />
            <Route path="/workbench" element={<WorkbenchPage />} />
            {/* Wave 41-48 Routes (v4.98-v5.21) */}
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/artifacts" element={<ArtifactsPage />} />
            <Route path="/attestations" element={<AttestationsPage />} />
            <Route path="/compliance" element={<CompliancePage />} />
            {/* Wave 49-56 Routes (v5.22-v5.45) */}
            <Route path="/datasets" element={<DatasetsPage />} />
            <Route path="/scenario-composer" element={<ScenarioComposerPage />} />
            <Route path="/reviews" element={<ReviewsPage />} />
            {/* Wave 65-67 Routes (v5.54.0-v5.56.0) */}
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/rooms" element={<RoomsPage />} />
            <Route path="/runbooks" element={<RunbooksPage />} />
            {/* Depth Wave Routes (v5.56.1-v5.60.0) */}
            <Route path="/evals" element={<EvalsPage />} />
          </Routes>
            </AppLayout>
          </PresentationProvider>
        </ToastProvider>
      </AppProvider>
    </BrowserRouter>
  );
}
