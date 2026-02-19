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
  runTestScenario,
  generateMRReviewBundle,
  analyzePipelineLog,
  buildArtifactPack,
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

  // ── v3.9 MR Review Bundle ─────────────────────────────────────────────────
  const [mrDiff, setMrDiff] = useState('');
  const [mrBundle, setMrBundle] = useState<any>(null);
  const [mrLoading, setMrLoading] = useState(false);

  const handleMRReview = async () => {
    setMrLoading(true);
    setMrBundle(null);
    const result = await generateMRReviewBundle(mrDiff || '+def hello(): pass\n');
    if (result) setMrBundle(result);
    setMrLoading(false);
  };

  // ── v3.9 Pipeline Analyzer ────────────────────────────────────────────────
  const [pipeLog, setPipeLog] = useState('');
  const [pipeResult, setPipeResult] = useState<any>(null);
  const [pipeLoading, setPipeLoading] = useState(false);

  const handlePipelineAnalyze = async () => {
    setPipeLoading(true);
    setPipeResult(null);
    const result = await analyzePipelineLog(pipeLog || 'All steps succeeded.');
    if (result) setPipeResult(result);
    setPipeLoading(false);
  };

  // ── v3.9 Artifacts ────────────────────────────────────────────────────────
  const [artifactResult, setArtifactResult] = useState<any>(null);
  const [artifactLoading, setArtifactLoading] = useState(false);

  const handleBuildArtifacts = async () => {
    setArtifactLoading(true);
    const md = mrBundle?.review_md || '# RiskCanvas DevOps Pack\nGenerated by v3.9+';
    const pipeJson = pipeResult ? JSON.stringify(pipeResult, null, 2) : undefined;
    const result = await buildArtifactPack(md, pipeJson);
    if (result) setArtifactResult(result);
    setArtifactLoading(false);
  };

  return (
    <div data-testid="devops-page" className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">DevOps Automations</h1>
        <p className="text-gray-600">v3.9+ Pro tools: MR Review, Pipeline Analyzer, Artifacts</p>
      </div>

      <Tabs defaultValue="risk-bot" className="w-full">
        <TabsList>
          <TabsTrigger value="risk-bot" data-testid="devops-tab-riskbot">Risk-Bot Report</TabsTrigger>
          <TabsTrigger value="gitlab" data-testid="devops-tab-gitlab">GitLab MR Bot</TabsTrigger>
          <TabsTrigger value="monitoring" data-testid="devops-tab-monitor">Monitor Reporter</TabsTrigger>
          <TabsTrigger value="test-harness" data-testid="devops-tab-harness">Test Harness</TabsTrigger>
          <TabsTrigger value="policy" data-testid="devops-tab-policy">Policy Gate</TabsTrigger>
          <TabsTrigger value="mr-review" data-testid="devops-tab-mr">MR Review</TabsTrigger>
          <TabsTrigger value="pipeline" data-testid="devops-tab-pipeline">Pipeline</TabsTrigger>
          <TabsTrigger value="artifacts" data-testid="devops-tab-artifacts">Artifacts</TabsTrigger>
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
                {policyLoading ? 'Evaluating...' : 'Evaluate Policy'}
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

        {/* MR Review Bundle Tab */}
        <TabsContent value="mr-review" data-testid="devops-panel-mr">
          <Card className="p-4 space-y-4">
            <h2 className="text-lg font-semibold">MR Review Bundle</h2>
            <p className="text-sm text-gray-600">Scan git diff for secrets, TODOs, bare excepts, and other findings.</p>
            <textarea
              className="w-full border rounded p-2 font-mono text-sm h-28"
              placeholder="Paste git diff (+lines)..."
              value={mrDiff}
              onChange={e => setMrDiff(e.target.value)}
              data-testid="devops-mr-diff-input"
            />
            <Button
              onClick={handleMRReview}
              disabled={mrLoading}
              data-testid="devops-mr-generate"
            >
              {mrLoading ? 'Analyzing...' : 'Generate Review Bundle'}
            </Button>

            {mrBundle && (
              <div data-testid="devops-mr-ready" className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant={mrBundle.decision === 'allow' ? 'default' : 'destructive'}>
                    {mrBundle.decision?.toUpperCase()}
                  </Badge>
                  <span className="text-sm text-gray-600">{mrBundle.summary}</span>
                </div>
                {mrBundle.review_json?.findings?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-1">
                      Findings ({mrBundle.review_json.findings.length})
                    </p>
                    <div className="space-y-1">
                      {mrBundle.review_json.findings.map((f: any, i: number) => (
                        <div key={i} className="flex items-center gap-2 text-sm">
                          <Badge variant={f.severity === 'blocker' ? 'destructive' : 'secondary'} className="text-xs">
                            {f.severity}
                          </Badge>
                          <span className="font-mono text-xs">[{f.code}]</span>
                          <span>{f.message}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <p className="text-xs text-gray-500 font-mono">Bundle hash: {mrBundle.bundle_hash}</p>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Pipeline Analyzer Tab */}
        <TabsContent value="pipeline" data-testid="devops-panel-pipeline">
          <Card className="p-4 space-y-4">
            <h2 className="text-lg font-semibold">Pipeline Failure Analyzer</h2>
            <p className="text-sm text-gray-600">Analyze CI/CD logs for OOM, timeouts, import errors, and more.</p>
            <textarea
              className="w-full border rounded p-2 font-mono text-sm h-28"
              placeholder="Paste pipeline log output..."
              value={pipeLog}
              onChange={e => setPipeLog(e.target.value)}
              data-testid="devops-pipe-log-input"
            />
            <Button
              onClick={handlePipelineAnalyze}
              disabled={pipeLoading}
              data-testid="devops-pipe-analyze"
            >
              {pipeLoading ? 'Analyzing...' : 'Analyze Pipeline Log'}
            </Button>

            {pipeResult && (
              <div data-testid="devops-pipe-ready" className="space-y-2">
                <div className="flex gap-2">
                  {pipeResult.categories?.map((cat: string) => (
                    <Badge key={cat} variant="destructive" className="text-xs">{cat}</Badge>
                  ))}
                  {pipeResult.categories?.length === 0 && (
                    <Badge variant="default" className="text-xs">CLEAN</Badge>
                  )}
                </div>
                <div className="flex gap-4 text-sm text-gray-600">
                  <span>Fatal: {pipeResult.fatal_count}</span>
                  <span>Error: {pipeResult.error_count}</span>
                  <span>Warning: {pipeResult.warning_count}</span>
                </div>
                {pipeResult.findings?.map((f: any, i: number) => (
                  <div key={i} className="border-l-4 border-red-400 pl-3 py-1">
                    <p className="text-xs font-semibold">[{f.category}] {f.message}</p>
                    <p className="text-xs text-gray-500">→ {f.remediation}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Artifacts Tab */}
        <TabsContent value="artifacts" data-testid="devops-panel-artifacts">
          <Card className="p-4 space-y-4">
            <h2 className="text-lg font-semibold">Artifact Pack Builder</h2>
            <p className="text-sm text-gray-600">
              Build a deterministic ZIP artifact pack from the latest MR review and pipeline analysis.
            </p>
            <Button
              onClick={handleBuildArtifacts}
              disabled={artifactLoading}
              data-testid="devops-artifacts-build"
            >
              {artifactLoading ? 'Building...' : 'Build Artifact Pack'}
            </Button>

            {artifactResult && (
              <div data-testid="devops-artifacts-ready" className="space-y-3">
                <p className="text-xs text-gray-500 font-mono">Manifest hash: {artifactResult.manifest_hash}</p>
                <p className="text-sm text-gray-600">
                  Files: {artifactResult.file_count}   Size: {(artifactResult.pack_size_bytes / 1024).toFixed(1)} KB
                </p>
                <div className="flex gap-2">
                  {artifactResult.file_list?.map((f: string) => (
                    <Badge key={f} variant="secondary" className="text-xs">{f}</Badge>
                  ))}
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  data-testid="devops-download-pack"
                  onClick={() => {
                    const bytes = Uint8Array.from(atob(artifactResult.pack_b64), c => c.charCodeAt(0));
                    const blob = new Blob([bytes], { type: 'application/zip' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url; a.download = `devops-pack-${artifactResult.manifest_hash?.slice(0, 8)}.zip`;
                    a.click(); URL.revokeObjectURL(url);
                  }}
                >
                  Download Pack
                </Button>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
