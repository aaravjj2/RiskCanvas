import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  createAgentConfig,
  listAgentConfigs,
  activateAgentConfig,
  runEvalHarness,
  listEvalReports,
} from '@/lib/api';

export default function GovernancePage() {
  const [configs, setConfigs] = useState<any[]>([]);
  const [evalReports, setEvalReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Create config form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newConfigName, setNewConfigName] = useState('');
  const [newConfigStrategy, setNewConfigStrategy] = useState('conservative');
  const [newConfigMaxLever, setNewConfigMaxLever] = useState(2.0);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    await Promise.all([loadConfigs(), loadEvalReports()]);
    setLoading(false);
  };

  const loadConfigs = async () => {
    const result = await listAgentConfigs();
    if (result) {
      setConfigs(result || []);
    }
  };

  const loadEvalReports = async () => {
    const result = await listEvalReports({ config_id: undefined });
    if (result) {
      setEvalReports(result || []);
    }
  };

  const handleCreateConfig = async () => {
    if (!newConfigName.trim()) {
      alert('Please enter config name');
      return;
    }

    setLoading(true);
    const result = await createAgentConfig({
      name: newConfigName,
      model: "gpt-4",
      provider: "openai",
      system_prompt: `You are a risk analysis agent with ${newConfigStrategy} strategy.`,
      tool_policies: {
        allowed_tools: ["portfolio_analysis", "var_calculation", "hedge_suggest"],
        max_iterations: 10
      },
      thresholds: {
        max_leverage: newConfigMaxLever,
        risk_tolerance: 0.05,
        strategy: newConfigStrategy
      },
      tags: ["test", newConfigStrategy]
    });

    if (result) {
      await loadAll();
      setShowCreateForm(false);
      setNewConfigName('');
    } else {
      setLoading(false);
    }
  };

  const handleActivate = async (configId: string) => {
    setLoading(true);
    await activateAgentConfig({ config_id: configId });
    await loadAll();
  };

  const handleRunEval = async (configId: string) => {
    setLoading(true);
    const result = await runEvalHarness({ config_id: configId });
    if (result) {
      await loadAll();
    } else {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-4" data-testid="governance-page">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Agent Governance</h1>
        <Button onClick={() => setShowCreateForm(!showCreateForm)} data-testid="toggle-create-form">
          {showCreateForm ? 'Cancel' : 'Create Config'}
        </Button>
      </div>

      {showCreateForm && (
        <Card className="p-4" data-testid="create-config-form">
          <h2 className="text-xl font-semibold mb-4">Create Agent Config</h2>
          <div className="space-y-3">
            <div>
              <Label htmlFor="name">Config Name</Label>
              <Input
                id="name"
                data-testid="config-name-input"
                value={newConfigName}
                onChange={(e) => setNewConfigName(e.target.value)}
                placeholder="E.g., Conservative Portfolio Agent"
              />
            </div>
            <div>
              <Label htmlFor="strategy">Strategy</Label>
              <select
                id="strategy"
                data-testid="strategy-select"
                value={newConfigStrategy}
                onChange={(e) => setNewConfigStrategy(e.target.value)}
                className="w-full p-2 border rounded"
              >
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
            <div>
              <Label htmlFor="maxLever">Max Leverage</Label>
              <Input
                id="maxLever"
                data-testid="max-leverage-input"
                type="number"
                step="0.1"
                value={newConfigMaxLever}
                onChange={(e) => setNewConfigMaxLever(parseFloat(e.target.value))}
              />
            </div>
            <Button onClick={handleCreateConfig} disabled={loading} data-testid="create-config-btn">
              {loading ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </Card>
      )}

      <Card className="p-4">
        <h2 className="text-xl font-semibold mb-4">Agent Configurations</h2>
        <div className="space-y-3" data-testid="configs-list">
          {loading && configs.length === 0 ? (
            <p className="text-gray-500" data-testid="configs-loading">Loading...</p>
          ) : configs.length === 0 ? (
            <p className="text-gray-500" data-testid="configs-empty">No configurations created yet.</p>
          ) : (
            configs.map((config) => (
              <Card key={config.config_id} className="p-3" data-testid={`config-${config.config_id}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold">{config.name}</h3>
                    <p className="text-sm text-gray-600">ID: {config.config_id}</p>
                    <p className="text-sm text-gray-600">
                      Model: {config.model} | Provider: {config.provider}
                    </p>
                    <p className="text-sm text-gray-600">
                      Strategy: {config.thresholds?.strategy || 'N/A'}
                    </p>
                    <p className="text-sm text-gray-600">
                      Status: <span className={config.status === 'active' ? 'text-green-600' : 'text-gray-500'}>
                        {config.status}
                      </span>
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleActivate(config.config_id)}
                      disabled={loading || config.status === 'active'}
                      data-testid={`activate-config-btn-${config.config_id}`}
                    >
                      Activate
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleRunEval(config.config_id)}
                      disabled={loading}
                      data-testid={`run-eval-btn-${config.config_id}`}
                    >
                      Run Eval
                    </Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </Card>

      <Card className="p-4">
        <h2 className="text-xl font-semibold mb-4">Evaluation Reports</h2>
        <div className="space-y-3" data-testid="eval-reports-list">
          {evalReports.length === 0 ? (
            <p className="text-gray-500">No evaluation reports yet.</p>
          ) : (
            evalReports.map((report) => (
              <Card key={report.report_id} className="p-3" data-testid={`eval-report-${report.report_id}`}>
                <h3 className="font-semibold">Report: {report.report_id}</h3>
                <p className="text-sm text-gray-600">Config: {report.config_id}</p>
                <p className="text-sm text-gray-600">
                  Score: {report.score} | Pass: {report.pass_count} | Fail: {report.fail_count}
                </p>
                <p className="text-sm text-gray-600">Executed at: {report.executed_at}</p>
              </Card>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
