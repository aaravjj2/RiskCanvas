import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { generateRiskBotReport } from '@/lib/api';

export default function DevOpsPage() {
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

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

  return (
    <div data-testid="devops-page" className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">DevOps Pack</h1>
        <p className="text-gray-600">CI-ready risk-bot reporting and automation tools</p>
      </div>

      {/* Generate Report */}
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

      {/* Report Display */}
      {report && (
        <Card className="p-4 mb-6" data-testid="riskbot-report-section">
          <h2 className="text-lg font-semibold mb-4">Latest Report</h2>
          <div className="space-y-4">
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-1">Report ID</p>
              <code className="text-xs bg-gray-100 p-2 rounded block overflow-x-auto">
                {report.report_id}
              </code>
            </div>

            {report.summary && (
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1">Summary</p>
                <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto whitespace-pre-wrap">
                  {report.summary}
                </pre>
              </div>
            )}

            {report.determinism_hashes && Object.keys(report.determinism_hashes).length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-2">Determinism Hashes</p>
                <div className="space-y-2">
                  {Object.entries(report.determinism_hashes).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <span className="text-xs font-medium min-w-32">{key}:</span>
                      <code className="text-xs bg-gray-100 p-1 rounded flex-1 overflow-x-auto">
                        {value as string}
                      </code>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {report.markdown && (
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-2">Markdown Output</p>
                <div className="border rounded p-3 max-h-96 overflow-y-auto bg-white">
                  <div
                    className="prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{ __html: report.markdown.replace(/\n/g, '<br/>') }}
                  />
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* CI-Ready Checklist */}
      <Card className="p-4" data-testid="ci-checklist">
        <h2 className="text-lg font-semibold mb-4">CI/CD Integration Checklist</h2>
        <ul className="space-y-2 text-sm">
          <li className="flex items-start gap-2">
            <span className="text-green-600 font-bold">✓</span>
            <span>Deterministic outputs: Same input → Same output (no random seeds)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 font-bold">✓</span>
            <span>SHA256 hashes for all artifacts (portfolios, runs, reports)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 font-bold">✓</span>
            <span>Sequence-based ordering (no real timestamps in deterministic mode)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 font-bold">✓</span>
            <span>Audit log for all operations with input/output hashes</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gray-400 font-bold">○</span>
            <span className="text-gray-500">GitHub Actions integration (placeholder)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gray-400 font-bold">○</span>
            <span className="text-gray-500">GitLab CI integration (placeholder)</span>
          </li>
        </ul>
      </Card>
    </div>
  );
}
