import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  generateRiskBotReport,
  analyzeGitLabMR,
  getGitLabComments,
  generateMonitoringReport,
  getMonitoringReports,
  runTestScenario
} from '@/lib/api';
import { ProvenanceDrawer } from '@/components/ProvenanceDrawer';

export default function DevOpsPage() {
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  
  // GitLab MR Bot state
  const [diffText, setDiffText] = useState('');
  const [mrAnalysis, setMrAnalysis] = useState<any>(null);
  const [comments, setComments] = useState<any[]>([]);
  
  // Monitor Reporter state
  const [monitorReport, setMonitorReport] = useState<any>(null);
  const [recentReports, setRecentReports] = useState<any[]>([]);
  
  // Test Harness state
  const [scenarioResult, setScenarioResult] = useState<any>(null);

  const handleGenerateReport = async () => {
    setLoading(true);
    const result = await generateRiskBotReport({
      scope: 'all',
      include_hashes: true,
    });
    if (result) {
      setReport(result);
    }
    setLoading(false);
  };

  const handleAnalyzeMR = async () => {
    setLoading(true);
    const result = await analyzeGitLabMR(diffText);
    if (result) {
      setMrAnalysis(result.analysis);
    }
    setLoading(false);
  };

  const handleLoadComments = async () => {
    const result = await getGitLabComments();
    if (result) {
      setComments(result.comments);
    }
  };

  const handleGenerateMonitorReport = async () => {
    setLoading(true);
    const result = await generateMonitoringReport({ include_health: true, include_coverage: true });
    if (result) {
      setMonitorReport(result);
    }
    setLoading(false);
  };

  const handleLoadMonitorReports = async () => {
    const result = await getMonitoringReports(10);
    if (result) {
      setRecentReports(result.reports);
    }
  };

  const handleRunScenario = async (scenarioType: 'mr_review' | 'monitoring_cycle') => {
    setLoading(true);
    const params: any = { scenario_type: scenarioType };
    if (scenarioType === 'mr_review' && diffText) {
      params.diff_text = diffText;
    }
    const result = await runTestScenario(params);
    if (result) {
      setScenarioResult(result);
    }
    setLoading(false);
  };

  // Policy Gate state
  const [policyDiff, setPolicyDiff] = useState('');
  const [policyResult, setPolicyResult] = useState<any>(null);
  const [policyExport, setPolicyExport] = useState<any>(null);
  const [policyLoading, setPolicyLoading] = useState(false);

  const handleEvaluatePolicy = async () => {
    setPolicyLoading(true);
    setPolicyResult(null);
    setPolicyExport(null);
    try {
      const res = await fetch('http://localhost:8090/devops/policy/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diff_text: policyDiff || '+def foo():\n+    pass\n' }),
      });
      if (res.ok) setPolicyResult(await res.json());
    } finally {
      setPolicyLoading(false);
    }
  };

  const handleExportMarkdown = async () => {
    try {
      const res = await fetch('http://localhost:8090/devops/policy/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diff_text: policyDiff || '+def foo():\n+    pass\n' }),
      });
      if (res.ok) setPolicyExport(await res.json());
    } catch {/**/}
  };

  const handleExportJson = async () => {
    await handleExportMarkdown();
  };

  return (
    <div data-testid="devops-page" className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">DevOps Automations</h1>
        <p className="text-gray-600">v2.5+ Agentic DevOps tools and automation</p>
      </div>

      <Tabs defaultValue="risk-bot" className="w-full">
        <TabsList>
          <TabsTrigger value="risk-bot" data-testid="devops-tab-riskbot">Risk-Bot Report</TabsTrigger>
          <TabsTrigger value="gitlab" data-testid="devops-tab-gitlab">GitLab MR Bot</TabsTrigger>
          <TabsTrigger value="monitoring" data-testid="devops-tab-monitor">Monitor Reporter</TabsTrigger>
          <TabsTrigger value="test-harness" data-testid="devops-tab-harness">Test Harness</TabsTrigger>
          <TabsTrigger value="policy" data-testid="devops-tab-policy">Policy Gate</TabsTrigger>
        </TabsList>

        {/* Risk-Bot Report Tab */}
        <TabsContent value="risk-bot" data-testid="devops-panel-riskbot">
          <Card className="p-4 mb-6">
            <h2 className="text-lg font-semibold mb-4">Risk-Bot CLI Report</h2>
            <p className="text-sm text-gray-600 mb-4">
              Generate a deterministic report for CI/CD pipelines. All outputs include SHA256 hashes for verification.
            </p>
            <Button
              onClick={handleGenerateReport}
              disabled={loading}
              data-testid="generate-riskbot-report-btn"
            >
              {loading ? 'Generating...' : 'Generate Report'}
            </Button>
          </Card>

          {report && (
            <Card className="p-4" data-testid="riskbot-report-section">
              <h2 className="text-lg font-semibold mb-4">Latest Report</h2>
              <div className="space-y-4">
                {report.report_markdown && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-1">Report</p>
                    <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto whitespace-pre-wrap">
                      {report.report_markdown}
                    </pre>
                  </div>
                )}
                {report.test_gate_summary && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-1">Test Gate</p>
                    <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(report.test_gate_summary, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </Card>
          )}
        </TabsContent>

        {/* GitLab MR Bot Tab */}
        <TabsContent value="gitlab" data-testid="devops-panel-gitlab">
          <Card className="p-4 mb-6">
            <h2 className="text-lg font-semibold mb-4">GitLab MR Bot</h2>
            <p className="text-sm text-gray-600 mb-4">
              Analyze code changes and post automated review comments (DEMO mode: offline only)
            </p>
            <textarea
              className="w-full border rounded p-3 mb-4 font-mono text-sm"
              rows={8}
              placeholder="Paste git diff here..."
              value={diffText}
              onChange={(e) => setDiffText(e.target.value)}
              data-testid="diff-input"
            />
            <div className="flex gap-2">
              <Button
                onClick={handleAnalyzeMR}
                disabled={loading || !diffText}
                data-testid="analyze-mr-btn"
              >
                Analyze MR
              </Button>
              <Button
                variant="outline"
                onClick={handleLoadComments}
                data-testid="load-comments-btn"
              >
                Load Offline Comments
              </Button>
            </div>
          </Card>

          {mrAnalysis && (
            <Card className="p-4 mb-6" data-testid="mr-analysis-section">
              <h3 className="font-semibold mb-2">Analysis Results</h3>
              <p className="text-sm text-gray-600">Total comments: {mrAnalysis.total_comments}</p>
              <div className="mt-4 space-y-2">
                {mrAnalysis.comments.map((comment: any, idx: number) => (
                  <div key={idx} className="border-l-4 border-yellow-400 pl-3 py-2">
                    <p className="text-xs font-semibold text-gray-700">Line {comment.line}</p>
                    <p className="text-sm text-gray-800">{comment.message}</p>
                    {comment.suggestion && (
                      <p className="text-xs text-gray-600 mt-1">→ {comment.suggestion}</p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {comments.length > 0 && (
            <Card className="p-4" data-testid="offline-comments-section">
              <h3 className="font-semibold mb-2">Offline Comments ({comments.length})</h3>
              <div className="space-y-2">
                {comments.map((comment, idx) => (
                  <div key={idx} className="bg-gray-50 p-3 rounded text-sm">
                    <p className="font-mono text-xs text-gray-600">MR #{comment.mr_iid}</p>
                    <p className="text-gray-800 mt-1">{comment.body}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </TabsContent>

        {/* Monitor Reporter Tab */}
        <TabsContent value="monitoring" data-testid="devops-panel-monitor">
          <Card className="p-4 mb-6">
            <h2 className="text-lg font-semibold mb-4">Monitor Reporter</h2>
            <p className="text-sm text-gray-600 mb-4">
              Generate automated health and coverage reports for system monitoring
            </p>
            <div className="flex gap-2">
              <Button
                onClick={handleGenerateMonitorReport}
                disabled={loading}
                data-testid="generate-monitor-report-btn"
              >
                Generate Report
              </Button>
              <Button
                variant="outline"
                onClick={handleLoadMonitorReports}
                data-testid="load-monitor-reports-btn"
              >
                Load Recent Reports
              </Button>
            </div>
          </Card>

          {monitorReport && (
            <Card className="p-4 mb-6" data-testid="monitor-report-section">
              <h3 className="font-semibold mb-2">Latest Monitoring Report</h3>
              <p className="font-mono text-xs text-gray-600">ID: {monitorReport.report_id}</p>
              {monitorReport.health && (
                <div className="mt-4">
                  <p className="text-sm font-semibold mb-2">Health Status</p>
                  <div className="space-y-1 text-sm">
                    <p>API: {monitorReport.health.api_status}</p>
                    <p>Database: {monitorReport.health.database}</p>
                    <p>Storage: {monitorReport.health.storage}</p>
                  </div>
                </div>
              )}
              {monitorReport.coverage && (
                <div className="mt-4">
                  <p className="text-sm font-semibold mb-2">Test Coverage</p>
                  <div className="space-y-1 text-sm">
                    <p>Pytest: {monitorReport.coverage.pytest_coverage}</p>
                    <p>E2E: {monitorReport.coverage.e2e_tests}</p>
                  </div>
                </div>
              )}
            </Card>
          )}

          {recentReports.length > 0 && (
            <Card className="p-4" data-testid="recent-reports-section">
              <h3 className="font-semibold mb-2">Recent Reports ({recentReports.length})</h3>
              <div className="space-y-2">
                {recentReports.map((rep, idx) => (
                  <div key={idx} className="bg-gray-50 p-3 rounded text-sm">
                    <p className="font-mono text-xs">{rep.report_id}</p>
                    <p className="text-xs text-gray-600">{rep.timestamp}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </TabsContent>

        {/* Test Harness Tab */}
        <TabsContent value="test-harness" data-testid="devops-panel-harness">
          <Card className="p-4 mb-6">
            <h2 className="text-lg font-semibold mb-4">Offline Test Harness</h2>
            <p className="text-sm text-gray-600 mb-4">
              Run offline test scenarios to validate DevOps automations locally
            </p>
            <div className="flex gap-2">
              <Button
                onClick={() => handleRunScenario('mr_review')}
                disabled={loading}
                data-testid="run-mr-scenario-btn"
              >
                Run MR Review Scenario
              </Button>
              <Button
                onClick={() => handleRunScenario('monitoring_cycle')}
                disabled={loading}
                data-testid="run-monitoring-scenario-btn"
              >
                Run Monitoring Scenario
              </Button>
            </div>
          </Card>

          {scenarioResult && (
            <Card className="p-4" data-testid="scenario-result-section">
              <h3 className="font-semibold mb-2">Scenario Result</h3>
              <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto">
                {JSON.stringify(scenarioResult, null, 2)}
              </pre>
            </Card>
          )}
        </TabsContent>

        {/* Policy Gate Tab */}
        <TabsContent value="policy" data-testid="devops-panel-policy">
          <Card className="p-4 mb-4">
            <h2 className="text-lg font-semibold mb-2">Policy Gate</h2>
            <p className="text-sm text-gray-600 mb-4">
              Evaluate a MR diff against the RiskCanvas policy ruleset (offline, deterministic).
            </p>
            <textarea
              className="w-full h-28 border rounded-md p-2 font-mono text-xs mb-3 bg-muted"
              placeholder="+def my_change():\n+    pass"
              value={policyDiff}
              onChange={e => setPolicyDiff(e.target.value)}
              data-testid="policy-diff-input"
            />
            <div className="flex gap-2">
              <Button
                onClick={handleEvaluatePolicy}
                disabled={policyLoading}
                data-testid="policy-evaluate-btn"
              >
                {policyLoading ? 'Evaluating…' : 'Evaluate Policy'}
              </Button>
              <Button variant="outline" onClick={handleExportMarkdown} data-testid="export-markdown-btn">
                Export Markdown
              </Button>
              <Button variant="outline" onClick={handleExportJson} data-testid="export-json-btn">
                Export JSON
              </Button>
            </div>
          </Card>

          {policyResult && (
            <Card className="p-4 mb-4" data-testid="policy-result-section">
              <div className="flex items-center gap-3 mb-3">
                <Badge
                  variant={policyResult.decision === 'allow' ? 'default' : 'destructive'}
                  data-testid="policy-result-badge"
                >
                  {policyResult.decision?.toUpperCase()}
                </Badge>
                <span className="text-sm font-medium">{policyResult.summary}</span>
              </div>
              {policyResult.reasons?.length > 0 && (
                <ul data-testid="policy-reasons-list" className="space-y-1">
                  {policyResult.reasons.map((r: any, i: number) => (
                    <li key={i} className="text-sm flex items-center gap-2">
                      <Badge variant={r.severity === 'blocker' ? 'destructive' : 'secondary'} className="text-xs">
                        {r.severity}
                      </Badge>
                      <span className="font-mono text-xs">[{r.code}]</span>
                      <span>{r.message}</span>
                    </li>
                  ))}
                </ul>
              )}
              {policyResult.run_id && (
                <div className="mt-3">
                  <ProvenanceDrawer kind="policy" resourceId={policyResult.run_id} label="Policy Provenance" />
                </div>
              )}
            </Card>
          )}

          {policyExport && (
            <Card className="p-4" data-testid="policy-export-section">
              <h3 className="font-semibold mb-2 text-sm">MR Comment Preview</h3>
              <pre className="text-xs bg-muted p-3 rounded overflow-x-auto whitespace-pre-wrap">
                {policyExport.mr_comment_markdown}
              </pre>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
