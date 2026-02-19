import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useApp } from "@/lib/context";
import { useEffect } from "react";
import { Play, CheckCircle2 } from "lucide-react";

export default function Dashboard() {
  const { portfolio, analysis, determinism, loading, loadFixture, runAnalysis, runDeterminismCheck } = useApp();

  // Auto-load fixture on mount if no portfolio
  useEffect(() => {
    if (portfolio.length === 0) {
      loadFixture();
    }
  }, [portfolio.length, loadFixture]);

  const varValue = analysis?.var?.var_value ?? 0;
  const confidence = analysis?.var?.confidence_level ?? 0.95;

  return (
    <div data-testid="dashboard-page">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Real-time risk analytics</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadFixture} variant="outline" data-testid="load-fixture-button">
            Load Fixture
          </Button>
          <Button onClick={runAnalysis} disabled={loading} data-testid="run-risk-button">
            {loading ? 'Running...' : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Run Analysis
              </>
            )}
          </Button>
          <Button onClick={runDeterminismCheck} disabled={loading} variant="outline" data-testid="determinism-button">
            Check Determinism
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card data-testid="kpi-portfolio-value">
          <CardHeader>
            <CardTitle className="text-sm">Portfolio Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold" data-testid="metric-value">
              ${analysis?.metrics.total_value.toFixed(2) ?? '0.00'}
            </div>
            <p className="text-xs text-muted-foreground">
              {analysis?.metrics.asset_count ?? 0} positions
            </p>
          </CardContent>
        </Card>
        
        <Card data-testid="kpi-var">
          <CardHeader>
            <CardTitle className="text-sm">VaR ({(confidence * 100).toFixed(0)}%)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold" data-testid="metric-var">
              ${varValue.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              {analysis?.var?.method ?? 'parametric'}
            </p>
          </CardContent>
        </Card>
        
        <Card data-testid="kpi-pnl">
          <CardHeader>
            <CardTitle className="text-sm">Total P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold" data-testid="metric-pnl">
              ${analysis?.metrics.total_pnl.toFixed(2) ?? '0.00'}
            </div>
            <p className="text-xs text-muted-foreground">
              Unrealized
            </p>
          </CardContent>
        </Card>
        
        <Card data-testid="kpi-determinism">
          <CardHeader>
            <CardTitle className="text-sm">Determinism</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2" data-testid="determinism-status">
              {determinism?.passed ? (
                <>
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <span className="text-sm font-semibold text-green-500">PASSED</span>
                </>
              ) : (
                <span className="text-sm text-muted-foreground">Not checked</span>
              )}
            </div>
            {determinism && (
              <p className="text-xs text-muted-foreground mt-1" data-testid="determinism-hash">
                {determinism.overall_hash.substring(0, 8)}...
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {analysis?.warnings && analysis.warnings.length > 0 && (
        <Card className="mb-6 border-yellow-500" data-testid="warnings-card">
          <CardHeader>
            <CardTitle className="text-sm text-yellow-500">Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside text-sm" data-testid="warnings-list">
              {analysis.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
      
      <div className="grid grid-cols-2 gap-4">
        <Card data-testid="chart-var-distribution">
          <CardHeader>
            <CardTitle>VaR Distribution</CardTitle>
            <CardDescription>Risk visualization</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-muted-foreground">
              Chart placeholder - Recharts integration pending
            </div>
          </CardContent>
        </Card>
        
        <Card data-testid="chart-top-contributors">
          <CardHeader>
            <CardTitle>Top Contributors</CardTitle>
            <CardDescription>Largest risk positions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-muted-foreground">
              Chart placeholder - Recharts integration pending
            </div>
          </CardContent>
        </Card>
      </div>

      {determinism && (
        <Card className="mt-4" data-testid="determinism-section">
          <CardHeader>
            <CardTitle>Determinism Report</CardTitle>
            <CardDescription>Hash verification results</CardDescription>
          </CardHeader>
          <CardContent>
            <table className="w-full" data-testid="determinism-table">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Check</th>
                  <th className="text-left py-2">Status</th>
                  <th className="text-left py-2">Hash</th>
                </tr>
              </thead>
              <tbody>
                {determinism.checks.map((c, i) => (
                  <tr key={c.name} className="border-b" data-testid={`det-row-${i}`}>
                    <td className="py-2">{c.name}</td>
                    <td className="py-2">{c.match ? '✓' : '✗'}</td>
                    <td className="py-2 font-mono text-xs">{c.hash}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
