import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { listRuns, compareRuns } from '@/lib/api';
import { useNavigate } from 'react-router-dom';

export default function RunHistory() {
  const [runs, setRuns] = useState<any[]>([]);
  const [selectedRuns, setSelectedRuns] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadRuns();
  }, []);

  const loadRuns = async () => {
    setLoading(true);
    const result = await listRuns({});
    if (result) {
      setRuns(result.runs || []);
    }
    setLoading(false);
  };

  const toggleRunSelection = (runId: string) => {
    if (selectedRuns.includes(runId)) {
      setSelectedRuns(selectedRuns.filter((id) => id !== runId));
    } else if (selectedRuns.length < 2) {
      setSelectedRuns([...selectedRuns, runId]);
    }
  };

  const handleCompare = async () => {
    if (selectedRuns.length !== 2) {
      alert('Please select exactly 2 runs to compare');
      return;
    }

    const [run1, run2] = selectedRuns;
    const result = await compareRuns(run1, run2);
    if (result) {
      navigate('/compare', { state: { comparison: result, run1, run2 } });
    }
  };

  const filteredRuns = runs.filter((r) =>
    r.run_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.portfolio_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="run-history-page" className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Run History</h1>
        <p className="text-gray-600">View and compare portfolio analysis runs</p>
      </div>

      <Card className="p-4">
        <div className="mb-4 flex gap-4">
          <Input
            data-testid="run-search-input"
            placeholder="Search by run ID or portfolio ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
          />
          <Button
            onClick={handleCompare}
            disabled={selectedRuns.length !== 2}
            data-testid="compare-runs-btn"
          >
            Compare Selected ({selectedRuns.length}/2)
          </Button>
        </div>

        <div className="overflow-x-auto" data-testid="runs-table">
          {loading && <p>Loading runs...</p>}
          {!loading && filteredRuns.length === 0 && (
            <p className="text-gray-500 text-center py-8">No runs found</p>
          )}
          {!loading && filteredRuns.length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Select</th>
                  <th className="text-left p-2">Run ID</th>
                  <th className="text-left p-2">Portfolio ID</th>
                  <th className="text-right p-2">Value</th>
                  <th className="text-right p-2">VaR 95%</th>
                  <th className="text-right p-2">VaR 99%</th>
                  <th className="text-center p-2">Deterministic</th>
                  <th className="text-center p-2">Sequence</th>
                </tr>
              </thead>
              <tbody>
                {filteredRuns.map((run) => {
                  const isSelected = selectedRuns.includes(run.run_id);
                  return (
                    <tr
                      key={run.run_id}
                      data-testid={`run-row-${run.run_id}`}
                      className={`border-b hover:bg-gray-50 cursor-pointer ${
                        isSelected ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => toggleRunSelection(run.run_id)}
                    >
                      <td className="p-2">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          readOnly
                          data-testid={`run-checkbox-${run.run_id}`}
                        />
                      </td>
                      <td className="p-2 font-mono text-xs">
                        {run.run_id.substring(0, 12)}...
                      </td>
                      <td className="p-2 font-mono text-xs">
                        {run.portfolio_id.substring(0, 12)}...
                      </td>
                      <td className="text-right p-2">
                        ${(run.value || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="text-right p-2">
                        ${(run.var95 || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="text-right p-2">
                        ${(run.var99 || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="text-center p-2">
                        {run.deterministic ? (
                          <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                            ✓
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                            -
                          </span>
                        )}
                      </td>
                      <td className="text-center p-2 font-mono text-xs">
                        #{run.sequence || 0}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
}
