import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import Dashboard from '@/pages/Dashboard';
import Portfolio from '@/pages/Portfolio';
import Scenarios from '@/pages/Scenarios';
import Agent from '@/pages/Agent';
import Reports from '@/pages/Reports';
import Settings from '@/pages/Settings';
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
          </Routes>
        </AppLayout>
      </AppProvider>
    </BrowserRouter>
  );
}
