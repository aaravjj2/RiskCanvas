import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  listMonitors,
  createMonitor,
  runMonitorNow,
  listAlerts,
  listDriftSummaries,
} from '@/lib/api';

export default function MonitoringPage() {
  const [monitors, setMonitors] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [driftSummaries, setDriftSummaries] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Create monitor form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newMonitorName, setNewMonitorName] = useState('');
  const [newMonitorPortfolioId, setNewMonitorPortfolioId] = useState('');
  const [newMonitorSchedule, setNewMonitorSchedule] = useState('daily');
  const [newMonitorVar95Threshold, setNewMonitorVar95Threshold] = useState(10000);
  const [newMonitorVar99Threshold, setNewMonitorVar99Threshold] = useState(15000);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    await Promise.all([loadMonitors(), loadAlerts(), loadDriftSummaries()]);
    setLoading(false);
  };

  const loadMonitors = async () => {
    const result = await listMonitors();
    if (result) {
      setMonitors(result.monitors || []);
    }
  };

  const loadAlerts = async () => {
    const result = await listAlerts({});
    if (result) {
      setAlerts(result.alerts || []);
    }
  };

  const loadDriftSummaries = async () => {
    const result = await listDriftSummaries({});
    if (result) {
      setDriftSummaries(result.summaries || []);
    }
  };

  const handleCreateMonitor = async () => {
    if (!newMonitorName.trim() || !newMonitorPortfolioId.trim()) {
      alert('Please enter monitor name and portfolio ID');
      return;
    }

    setLoading(true);
    const result = await createMonitor({
      name: newMonitorName,
      portfolio_id: newMonitorPortfolioId,
      schedule: newMonitorSchedule,
      thresholds: {
        var95: newMonitorVar95Threshold,
        var99: newMonitorVar99Threshold,
      },
    });

    if (result) {
      await loadAll();
      setShowCreateForm(false);
      setNewMonitorName('');
      setNewMonitorPortfolioId('');
      alert(`Monitor created with ID: ${result.monitor_id}`);
    }
    setLoading(false);
  };

  const handleRunNow = async (monitorId: string) => {
    setLoading(true);
    const result = await runMonitorNow(monitorId, {});
    if (result) {
      alert(`Monitor executed! Run ID: ${result.run_id}`);
      await loadAll();
    }
    setLoading(false);
  };

  return (
    <div data-testid="monitoring-page" className="p-6">
      <div className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Monitoring</h1>
          <p className="text-gray-600">Schedule risk monitoring with alerts and drift detection</p>
        </div>
        <Button
          onClick={() => setShowCreateForm(!showCreateForm)}
          data-testid="toggle-create-monitor-btn"
        >
          {showCreateForm ? 'Cancel' : 'Create Monitor'}
        </Button>
      </div>

      {/* Create Monitor Form */}
      {showCreateForm && (
        <Card className="p-4 mb-6" data-testid="create-monitor-form">
          <h2 className="text-lg font-semibold mb-4">Create New Monitor</h2>
          <div className="space-y-4">
            <div>
              <Label htmlFor="monitor-name">Monitor Name</Label>
              <Input
                id="monitor-name"
                data-testid="monitor-name-input"
                placeholder="Daily VaR Check"
                value={newMonitorName}
                onChange={(e) => setNewMonitorName(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="monitor-portfolio">Portfolio ID</Label>
              <Input
                id="monitor-portfolio"
                data-testid="monitor-portfolio-input"
                placeholder="portfolio-abc123..."
                value={newMonitorPortfolioId}
                onChange={(e) => setNewMonitorPortfolioId(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="monitor-schedule">Schedule</Label>
              <select
                id="monitor-schedule"
                data-testid="monitor-schedule-select"
                value={newMonitorSchedule}
                onChange={(e) => setNewMonitorSchedule(e.target.value)}
                className="w-full border rounded p-2"
              >
                <option value="hourly">Hourly</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="var95-threshold">VaR 95% Threshold ($)</Label>
                <Input
                  id="var95-threshold"
                  data-testid="var95-threshold-input"
                  type="number"
                  value={newMonitorVar95Threshold}
                  onChange={(e) => setNewMonitorVar95Threshold(Number(e.target.value))}
                />
              </div>
              <div>
                <Label htmlFor="var99-threshold">VaR 99% Threshold ($)</Label>
                <Input
                  id="var99-threshold"
                  data-testid="var99-threshold-input"
                  type="number"
                  value={newMonitorVar99Threshold}
                  onChange={(e) => setNewMonitorVar99Threshold(Number(e.target.value))}
                />
              </div>
            </div>
            <Button
              onClick={handleCreateMonitor}
              disabled={loading}
              data-testid="create-monitor-btn"
              className="w-full"
            >
              {loading ? 'Creating...' : 'Create Monitor'}
            </Button>
          </div>
        </Card>
      )}

      {/* Monitors List */}
      <Card className="p-4 mb-6">
        <h2 className="text-lg font-semibold mb-4">Active Monitors</h2>
        <div className="space-y-3" data-testid="monitors-list">
          {loading && <p>Loading monitors...</p>}
          {!loading && monitors.length === 0 && (
            <p className="text-gray-500 text-center py-8">No monitors configured</p>
          )}
          {!loading &&
            monitors.map((monitor) => (
              <Card
                key={monitor.monitor_id}
                data-testid={`monitor-item-${monitor.monitor_id}`}
                className="p-4 border"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{monitor.name}</h3>
                    <p className="text-sm text-gray-600 mb-2">
                      Portfolio: {monitor.portfolio_id} | Schedule: {monitor.schedule}
                    </p>
                    <div className="flex gap-4 text-sm">
                      <span>
                        <strong>VaR 95% Threshold:</strong> ${monitor.thresholds?.var95?.toLocaleString()}
                      </span>
                      <span>
                        <strong>VaR 99% Threshold:</strong> ${monitor.thresholds?.var99?.toLocaleString()}
                      </span>
                    </div>
                    {monitor.last_run_id && (
                      <p className="text-xs text-gray-500 mt-2">
                        Last run: {monitor.last_run_id.substring(0, 12)}... (Sequence #{monitor.last_sequence || 0})
                      </p>
                    )}
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleRunNow(monitor.monitor_id)}
                    disabled={loading}
                    data-testid={`run-now-btn-${monitor.monitor_id}`}
                  >
                    Run Now
                  </Button>
                </div>
              </Card>
            ))}
        </div>
      </Card>

      {/* Alerts Section */}
      <Card className="p-4 mb-6" data-testid="alerts-section">
        <h2 className="text-lg font-semibold mb-4">Recent Alerts</h2>
        <div className="space-y-2">
          {alerts.length === 0 && (
            <p className="text-gray-500 text-center py-4">No alerts triggered</p>
          )}
          {alerts.slice(0, 10).map((alert) => (
            <div
              key={alert.alert_id}
              data-testid={`alert-item-${alert.alert_id}`}
              className="p-3 border rounded flex justify-between items-start"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`px-2 py-1 text-xs rounded font-semibold ${
                      alert.severity === 'critical'
                        ? 'bg-red-600 text-white'
                        : alert.severity === 'high'
                        ? 'bg-orange-500 text-white'
                        : alert.severity === 'medium'
                        ? 'bg-yellow-500 text-white'
                        : 'bg-blue-500 text-white'
                    }`}
                  >
                    {alert.severity?.toUpperCase()}
                  </span>
                  <span className="text-sm font-medium">{alert.metric}</span>
                </div>
                <p className="text-sm text-gray-600">{alert.message}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Monitor: {alert.monitor_id} | Run: {alert.run_id?.substring(0, 12)}...
                </p>
              </div>
              <span className="text-xs text-gray-500">Seq #{alert.sequence}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Drift Summaries */}
      <Card className="p-4" data-testid="drift-summaries-section">
        <h2 className="text-lg font-semibold mb-4">Drift Summaries</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {driftSummaries.length === 0 && (
            <p className="text-gray-500 text-center py-4 col-span-2">No drift detected</p>
          )}
          {driftSummaries.slice(0, 6).map((drift) => (
            <Card
              key={drift.drift_id}
              data-testid={`drift-summary-${drift.drift_id}`}
              className="p-4 border"
            >
              <h3 className="font-semibold mb-2">Monitor: {drift.monitor_id.substring(0, 12)}...</h3>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Drift Score:</span>
                  <span className="font-semibold">{drift.drift_score?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Changed Assets:</span>
                  <span>{drift.changed_assets?.length || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">VaR Change:</span>
                  <span className={drift.var_delta >= 0 ? 'text-red-600' : 'text-green-600'}>
                    ${drift.var_delta?.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Run 1: {drift.run1_id?.substring(0, 12)}... → Run 2: {drift.run2_id?.substring(0, 12)}...
                </p>
              </div>
            </Card>
          ))}
        </div>
      </Card>
    </div>
  );
}
