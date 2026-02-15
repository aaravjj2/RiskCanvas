import { useLocation } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function ComparePage() {
  const location = useLocation();
  const { comparison, run1, run2 } = location.state || {};

  if (!comparison) {
    return (
      <div className="p-6" data-testid="compare-page">
        <Card className="p-6">
          <p className="text-center text-gray-500">
            No comparison data available. Please select two runs from Run History.
          </p>
        </Card>
      </div>
    );
  }

  const formatNumber = (num: number) => {
    return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const formatDelta = (delta: number) => {
    const sign = delta >= 0 ? '+' : '';
    return `${sign}${formatNumber(delta)}`;
  };

  const getDeltaColor = (delta: number, isRisk: boolean = false) => {
    // For risk metrics, negative is good (reduced risk)
    // For value, positive is good (increased value)
    if (delta === 0) return 'text-gray-600';
    const isGood = isRisk ? delta < 0 : delta > 0;
    return isGood ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div data-testid="compare-page" className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Run Comparison</h1>
        <p className="text-gray-600">
          Comparing Run 1 ({run1?.substring(0, 12)}...) vs Run 2 ({run2?.substring(0, 12)}...)
        </p>
      </div>

      {/* Delta KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card className="p-4" data-testid="delta-card-value">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Portfolio Value Change</h3>
          <p className={`text-2xl font-bold ${getDeltaColor(comparison.deltas?.value || 0)}`}>
            ${formatDelta(comparison.deltas?.value || 0)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {comparison.run1?.value ? `$${formatNumber(comparison.run1.value)}` : '-'} → {comparison.run2?.value ? `$${formatNumber(comparison.run2.value)}` : '-'}
          </p>
        </Card>

        <Card className="p-4" data-testid="delta-card-var95">
          <h3 className="text-sm font-medium text-gray-500 mb-2">VaR 95% Change</h3>
          <p className={`text-2xl font-bold ${getDeltaColor(comparison.deltas?.var95 || 0, true)}`}>
            ${formatDelta(comparison.deltas?.var95 || 0)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {comparison.run1?.var95 ? `$${formatNumber(comparison.run1.var95)}` : '-'} → {comparison.run2?.var95 ? `$${formatNumber(comparison.run2.var95)}` : '-'}
          </p>
        </Card>

        <Card className="p-4" data-testid="delta-card-var99">
          <h3 className="text-sm font-medium text-gray-500 mb-2">VaR 99% Change</h3>
          <p className={`text-2xl font-bold ${getDeltaColor(comparison.deltas?.var99 || 0, true)}`}>
            ${formatDelta(comparison.deltas?.var99 || 0)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {comparison.run1?.var99 ? `$${formatNumber(comparison.run1.var99)}` : '-'} → {comparison.run2?.var99 ? `$${formatNumber(comparison.run2.var99)}` : '-'}
          </p>
        </Card>
      </div>

      {/* Top Changes Table */}
      <Card className="p-4">
        <h2 className="text-lg font-semibold mb-4">Top Contributing Changes</h2>
        <div className="overflow-x-auto" data-testid="top-changes-table">
          {comparison.top_changes && comparison.top_changes.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Asset</th>
                  <th className="text-right p-2">Run 1 Value</th>
                  <th className="text-right p-2">Run 2 Value</th>
                  <th className="text-right p-2">Change</th>
                  <th className="text-right p-2">% Change</th>
                </tr>
              </thead>
              <tbody>
                {comparison.top_changes.map((change: any, idx: number) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="p-2 font-medium">{change.asset || change.symbol}</td>
                    <td className="text-right p-2">${formatNumber(change.value_run1 || 0)}</td>
                    <td className="text-right p-2">${formatNumber(change.value_run2 || 0)}</td>
                    <td className={`text-right p-2 font-semibold ${getDeltaColor(change.delta || 0)}`}>
                      ${formatDelta(change.delta || 0)}
                    </td>
                    <td className={`text-right p-2 ${getDeltaColor(change.pct_change || 0)}`}>
                      {formatDelta(change.pct_change || 0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500 text-center py-4">No asset-level changes available</p>
          )}
        </div>
      </Card>

      <div className="mt-6 flex gap-4">
        <Button onClick={() => window.history.back()} data-testid="back-to-history-btn">
          Back to Run History
        </Button>
      </div>
    </div>
  );
}
