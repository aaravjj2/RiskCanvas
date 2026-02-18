import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  createAgentConfig,
  listAgentConfigs,
  activateAgentConfig,
  runEvalHarness,
  listEvalReports,
  evaluatePolicy,
  validateNarrative,
  listEvalSuites,
  runEvalSuite,
  getScorecardMd,
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

  // ── v3.7 Policy Engine ────────────────────────────────────────────────────
  const [policyTools, setPolicyTools] = useState<string[]>(['portfolio_analysis', 'var_calculation']);
  const [policyCallCount, setPolicyCallCount] = useState(5);
  const [policyResult, setPolicyResult] = useState<any>(null);
  const [policyLoading, setPolicyLoading] = useState(false);

  const handleEvaluatePolicy = async () => {
    setPolicyLoading(true);
    setPolicyResult(null);
    const result = await evaluatePolicy({ tools: policyTools, tool_calls_requested: policyCallCount });
    if (result) setPolicyResult(result);
    setPolicyLoading(false);
  };

  // ── v3.7 Narrative Validator ──────────────────────────────────────────────
  const [narrativeText, setNarrativeText] = useState('');
  const [narrativeJson, setNarrativeJson] = useState('{"portfolio_value": 18250.75}');
  const [narrativeResult, setNarrativeResult] = useState<any>(null);
  const [narrativeLoading, setNarrativeLoading] = useState(false);

  const handleValidateNarrative = async () => {
    setNarrativeLoading(true);
    setNarrativeResult(null);
    let computed: any = {};
    try { computed = JSON.parse(narrativeJson); } catch { computed = {}; }
    const result = await validateNarrative(narrativeText, computed);
    if (result) setNarrativeResult(result);
    setNarrativeLoading(false);
  };

  // ── v3.8 Eval Suites ──────────────────────────────────────────────────────
  const [suites, setSuites] = useState<any[]>([]);
  const [suiteRunResults, setSuiteRunResults] = useState<Record<string, any>>({});
  const [scorecardMd, setScorecardMd] = useState<string>('');
  const [suitesLoading, setSuitesLoading] = useState(false);

  const loadSuites = async () => {
    setSuitesLoading(true);
    const result = await listEvalSuites();
    if (result) setSuites(result.suites || []);
    setSuitesLoading(false);
  };

  const handleRunSuite = async (suiteId: string) => {
    setSuitesLoading(true);
    const result = await runEvalSuite(suiteId);
    if (result) {
      setSuiteRunResults(prev => ({ ...prev, [suiteId]: result }));
      const md = await getScorecardMd(result.run_id);
      setScorecardMd(md || '');
    }
    setSuitesLoading(false);
  };

  return (
    <div className="p-4 space-y-4" data-testid="governance-page">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Agent Governance</h1>
        <Badge variant="secondary">v4.0</Badge>
      </div>

      <Tabs defaultValue="configs" className="w-full">
        <TabsList>
          <TabsTrigger value="configs">Agent Configs</TabsTrigger>
          <TabsTrigger value="policy" data-testid="gov-tab-policy">Policy v2</TabsTrigger>
          <TabsTrigger value="narrative" data-testid="gov-tab-narrative">Narrative</TabsTrigger>
          <TabsTrigger value="suites" data-testid="gov-tab-suites">Eval Suites</TabsTrigger>
        </TabsList>

        {/* Existing Configs Tab */}
        <TabsContent value="configs">
          <div className="space-y-4">
            <div className="flex justify-end">
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
        </TabsContent>

        {/* Policy v2 Tab */}
        <TabsContent value="policy">
          <Card className="p-4 space-y-4" data-testid="gov-policy-panel">
            <h2 className="text-lg font-semibold">Policy Engine v2</h2>
            <p className="text-sm text-gray-600">Evaluate tool allowlists, call budgets, and response sizes.</p>

            <div className="space-y-2">
              <Label>Tools (comma-separated)</Label>
              <Input
                data-testid="gov-tools-input"
                value={policyTools.join(', ')}
                onChange={e => setPolicyTools(e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
                placeholder="portfolio_analysis, var_calculation"
              />
              <Label>Tool calls requested</Label>
              <Input
                data-testid="gov-calls-input"
                type="number"
                value={policyCallCount}
                onChange={e => setPolicyCallCount(parseInt(e.target.value) || 0)}
              />
              <Button
                onClick={handleEvaluatePolicy}
                disabled={policyLoading}
                data-testid="gov-validate-btn"
              >
                {policyLoading ? 'Evaluating…' : 'Evaluate Policy'}
              </Button>
            </div>

            {policyResult && (
              <div data-testid="gov-validate-result" className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge
                    data-testid="gov-policy-ready"
                    variant={policyResult.decision === 'allow' ? 'default' : 'destructive'}
                  >
                    {policyResult.decision?.toUpperCase()}
                  </Badge>
                  <span className="text-sm text-gray-600">Mode: {policyResult.mode}</span>
                </div>
                {policyResult.reasons?.length > 0 && (
                  <ul className="space-y-1">
                    {policyResult.reasons.map((r: any, i: number) => (
                      <li key={i} className="text-sm">
                        <Badge variant="secondary" className="mr-1">{r.code}</Badge>
                        {r.message}
                      </li>
                    ))}
                  </ul>
                )}
                <p className="text-xs text-gray-500 font-mono">
                  Policy hash: {policyResult.policy_hash}
                </p>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Narrative Validator Tab */}
        <TabsContent value="narrative">
          <Card className="p-4 space-y-4" data-testid="gov-narrative-panel">
            <h2 className="text-lg font-semibold">Narrative Validator</h2>
            <p className="text-sm text-gray-600">
              Verify that numbers cited in narrative text match computed results (±1% tolerance).
            </p>
            <div>
              <Label>Computed results (JSON)</Label>
              <textarea
                className="w-full border rounded p-2 font-mono text-sm h-20"
                data-testid="gov-computed-json"
                value={narrativeJson}
                onChange={e => setNarrativeJson(e.target.value)}
                placeholder='{"portfolio_value": 18250.75}'
              />
            </div>
            <div>
              <Label>Narrative text</Label>
              <textarea
                className="w-full border rounded p-2 text-sm h-24"
                data-testid="gov-narrative-text"
                value={narrativeText}
                onChange={e => setNarrativeText(e.target.value)}
                placeholder="The portfolio value is 18250.75 USD..."
              />
            </div>
            <Button
              onClick={handleValidateNarrative}
              disabled={narrativeLoading}
              data-testid="gov-validate-narrative-btn"
            >
              {narrativeLoading ? 'Validating…' : 'Validate Narrative'}
            </Button>

            {narrativeResult && (
              <div data-testid="gov-narrative-result" className="space-y-2">
                <Badge
                  variant={narrativeResult.valid ? 'default' : 'destructive'}
                  data-testid="gov-narrative-badge"
                >
                  {narrativeResult.valid ? 'VALID' : 'INVALID'}
                </Badge>
                {narrativeResult.unknown_numbers?.length > 0 && (
                  <p className="text-sm text-red-600">
                    Unknown numbers: {narrativeResult.unknown_numbers.join(', ')}
                  </p>
                )}
                {narrativeResult.remediation && (
                  <p className="text-sm text-gray-600">{narrativeResult.remediation}</p>
                )}
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Eval Suites Tab */}
        <TabsContent value="suites">
          <Card className="p-4 space-y-4" data-testid="gov-suites-panel">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Eval Suites v2</h2>
              <Button
                variant="outline"
                onClick={loadSuites}
                disabled={suitesLoading}
                data-testid="gov-load-suites-btn"
              >
                {suitesLoading ? 'Loading…' : 'Load Suites'}
              </Button>
            </div>

            {suites.length > 0 && (
              <div data-testid="eval-suites-list" className="space-y-2">
                {suites.map((suite) => (
                  <div
                    key={suite.suite_id}
                    className="flex items-center justify-between border rounded p-3"
                  >
                    <div>
                      <p className="font-medium text-sm">{suite.label}</p>
                      <p className="text-xs text-gray-500">{suite.suite_id} · {suite.case_count} cases</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {suiteRunResults[suite.suite_id] && (
                        <Badge data-testid={`eval-result-${suite.suite_id}`}>
                          {suiteRunResults[suite.suite_id].pass_rate}
                        </Badge>
                      )}
                      <Button
                        size="sm"
                        onClick={() => handleRunSuite(suite.suite_id)}
                        disabled={suitesLoading}
                        data-testid={`eval-run-btn-${suite.suite_id}`}
                      >
                        Run
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {scorecardMd && (
              <div data-testid="eval-scorecard-ready" className="space-y-2">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium text-sm">Latest Scorecard</h3>
                  <Button
                    size="sm"
                    variant="outline"
                    data-testid="eval-export-md"
                    onClick={() => {
                      const blob = new Blob([scorecardMd], { type: 'text/markdown' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url; a.download = 'scorecard.md'; a.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    Export MD
                  </Button>
                </div>
                <pre className="text-xs bg-gray-50 border rounded p-3 overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto">
                  {scorecardMd}
                </pre>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
