import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Database } from "lucide-react";
import { listReports, getReportDownloadUrls } from "@/lib/api";

interface Report {
  bundle_id: string;
  run_id: string;
  created_at: string;
  has_storage: boolean;
}

export default function Reports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const storageProvider = "LocalStorage"; // DEMO mode default

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    setLoading(true);
    const result = await listReports();
    if (result && result.reports) {
      setReports(result.reports);
    }
    setLoading(false);
  };

  const handleGenerateReport = async () => {
    // For now, just placeholder - user would select a run first
    alert("Please select a run from Run History to generate a report");
  };

  const handleDownloadReport = async (bundleId: string) => {
    const urls = await getReportDownloadUrls(bundleId);
    if (urls && urls.download_urls) {
      // Open HTML report in new tab
      const htmlUrl = urls.download_urls.find((u: any) => u.file === 'report.html');
      if (htmlUrl) {
        window.open(htmlUrl.url, '_blank');
      }
    }
  };

  return (
    <div data-testid="reports-page" className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Reports</h1>
          <p className="text-gray-600">View and download past reports</p>
        </div>
        <div className="flex items-center gap-2" data-testid="storage-provider-badge">
          <Database className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-600">{storageProvider}</span>
        </div>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Report History</CardTitle>
          <CardDescription>All generated report bundles with storage integration</CardDescription>
        </CardHeader>
        <CardContent>
          <div data-testid="reports-list" className="space-y-4">
            {loading && (
              <div className="text-muted-foreground text-center py-8">
                Loading reports...
              </div>
            )}
            
            {!loading && reports.length === 0 && (
              <div className="text-muted-foreground text-center py-8">
                No reports generated yet
              </div>
            )}
            
            {!loading && reports.length > 0 && reports.map((report) => (
              <div 
                key={report.bundle_id} 
                className="border rounded-lg p-4 flex items-center justify-between"
                data-testid={`report-${report.bundle_id}`}
              >
                <div>
                  <p className="font-semibold">{report.bundle_id}</p>
                  <p className="text-sm text-gray-600">Run: {report.run_id}</p>
                  <p className="text-xs text-gray-500">{report.created_at}</p>
                </div>
                <div className="flex items-center gap-2">
                  {report.has_storage && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownloadReport(report.bundle_id)}
                      data-testid={`download-report-${report.bundle_id}`}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-6 pt-6 border-t border-border">
            <Button 
              onClick={handleGenerateReport}
              data-testid="generate-report-button"
            >
              <Download className="h-4 w-4 mr-2" />
              Generate New Report
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
