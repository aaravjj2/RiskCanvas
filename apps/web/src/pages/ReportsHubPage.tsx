import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { listReports, buildReportBundle } from '@/lib/api';

export default function ReportsHubPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [portfolioFilter, setPortfolioFilter] = useState('');
  const [runFilter, setRunFilter] = useState('');

  useEffect(() => {
    loadReports();
  }, [portfolioFilter, runFilter]);

  const loadReports = async () => {
    setLoading(true);
    const filters: any = {};
    if (portfolioFilter) filters.portfolio_id = portfolioFilter;
    if (runFilter) filters.run_id = runFilter;

    const result = await listReports(filters);
    if (result) {
      setReports(result.reports || []);
    }
    setLoading(false);
  };

  const handleBuildBundle = async (runId: string) => {
    setLoading(true);
    const result = await buildReportBundle({ run_id: runId });
    if (result) {
      alert(`Report bundle created! Bundle ID: ${result.report_bundle_id}`);
      await loadReports();
    }
    setLoading(false);
  };

  const handleOpenReport = (reportUrl: string) => {
    window.open(reportUrl, '_blank');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard');
  };

  const filteredReports = reports.filter((r) => {
    if (portfolioFilter && !r.portfolio_id?.includes(portfolioFilter)) return false;
    if (runFilter && !r.run_id?.includes(runFilter)) return false;
    return true;
  });

  return (
    <div data-testid="reports-hub-page" className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Reports Hub</h1>
        <p className="text-gray-600">View, build, and download report bundles with deterministic hashes</p>
      </div>

      {/* Filters */}
      <Card className="p-4 mb-6">
        <h2 className="text-lg font-semibold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Input
              data-testid="filter-portfolio-input"
              placeholder="Filter by Portfolio ID..."
              value={portfolioFilter}
              onChange={(e) => setPortfolioFilter(e.target.value)}
            />
          </div>
          <div>
            <Input
              data-testid="filter-run-input"
              placeholder="Filter by Run ID..."
              value={runFilter}
              onChange={(e) => setRunFilter(e.target.value)}
            />
          </div>
        </div>
      </Card>

      {/* Build Bundle Section */}
      <Card className="p-4 mb-6">
        <h2 className="text-lg font-semibold mb-4">Build Report Bundle</h2>
        <p className="text-sm text-gray-600 mb-4">
          Create a report bundle (HTML + JSON) with SHA256 hashes for a specific run.
        </p>
        <div className="flex gap-4">
          <Input
            data-testid="build-bundle-run-id-input"
            placeholder="Enter Run ID..."
            className="flex-1"
            id="build-bundle-run-id"
          />
          <Button
            onClick={() => {
              const input = document.getElementById('build-bundle-run-id') as HTMLInputElement;
              if (input?.value) {
                handleBuildBundle(input.value);
              } else {
                alert('Please enter a Run ID');
              }
            }}
            disabled={loading}
            data-testid="build-report-bundle-btn"
          >
            {loading ? 'Building...' : 'Build Bundle'}
          </Button>
        </div>
      </Card>

      {/* Reports List */}
      <Card className="p-4">
        <h2 className="text-lg font-semibold mb-4">All Reports</h2>
        <div className="space-y-4" data-testid="reports-list">
          {loading && <p>Loading reports...</p>}
          {!loading && filteredReports.length === 0 && (
            <p className="text-gray-500 text-center py-8">No reports found</p>
          )}
          {!loading &&
            filteredReports.map((report) => (
              <Card
                key={report.report_bundle_id || report.report_id}
                data-testid={`report-card-${report.report_bundle_id || report.report_id}`}
                className="p-4 border"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">
                      Report for Run: {report.run_id?.substring(0, 12)}...
                    </h3>
                    <p className="text-sm text-gray-600">
                      Portfolio: {report.portfolio_id?.substring(0, 12)}...
                    </p>
                  </div>
                  {report.report_bundle_id && (
                    <span className="px-3 py-1 bg-green-100 text-green-800 text-xs rounded font-semibold">
                      BUNDLED
                    </span>
                  )}
                </div>

                {report.report_bundle_id && (
                  <div className="space-y-2 mb-4">
                    <div>
                      <p className="text-xs font-semibold text-gray-600 mb-1">Report Bundle ID</p>
                      <div className="flex gap-2 items-center">
                        <code className="text-xs bg-gray-100 p-1 rounded flex-1 overflow-x-auto">
                          {report.report_bundle_id}
                        </code>
                        <button
                          onClick={() => copyToClipboard(report.report_bundle_id)}
                          className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                          data-testid={`copy-bundle-id-${report.report_bundle_id}`}
                        >
                          Copy
                        </button>
                      </div>
                    </div>

                    {report.html_hash && (
                      <div>
                        <p className="text-xs font-semibold text-gray-600 mb-1">HTML Hash (SHA256)</p>
                        <div className="flex gap-2 items-center">
                          <code className="text-xs bg-gray-100 p-1 rounded flex-1 overflow-x-auto">
                            {report.html_hash}
                          </code>
                          <button
                            onClick={() => copyToClipboard(report.html_hash)}
                            className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                          >
                            Copy
                          </button>
                        </div>
                      </div>
                    )}

                    {report.json_hash && (
                      <div>
                        <p className="text-xs font-semibold text-gray-600 mb-1">JSON Hash (SHA256)</p>
                        <div className="flex gap-2 items-center">
                          <code className="text-xs bg-gray-100 p-1 rounded flex-1 overflow-x-auto">
                            {report.json_hash}
                          </code>
                          <button
                            onClick={() => copyToClipboard(report.json_hash)}
                            className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                          >
                            Copy
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex gap-2">
                  {report.html_url && (
                    <Button
                      size="sm"
                      onClick={() => handleOpenReport(report.html_url)}
                      data-testid={`open-report-btn-${report.report_bundle_id || report.report_id}`}
                    >
                      Open HTML Report
                    </Button>
                  )}
                  {report.html_url && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => window.open(report.html_url, '_blank')}
                      data-testid={`download-html-btn-${report.report_bundle_id || report.report_id}`}
                    >
                      Download HTML
                    </Button>
                  )}
                  {report.json_url && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => window.open(report.json_url, '_blank')}
                      data-testid={`download-json-btn-${report.report_bundle_id || report.report_id}`}
                    >
                      Download JSON
                    </Button>
                  )}
                </div>
              </Card>
            ))}
        </div>
      </Card>
    </div>
  );
}
