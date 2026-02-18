import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { listRuns, compareRuns, getRunStatus } from '@/lib/api';
import { useNavigate } from 'react-router-dom';
import { ProvenanceDrawer } from '@/components/ProvenanceDrawer';

const STAGE_LABELS: Record<string, string> = {
  NOT_STARTED: 'Not Started',
  VALIDATE: 'Validating',
  PRICE: 'Pricing',
  VAR: 'VaR',
  REPORT: 'Report',
  DONE: 'Done',
};

function LiveRunPanel({ runId }: { runId: string }) {
  const [status, setStatus] = useState<any>(null);
  const [sseConnected, setSseConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  const loadStatus = async () => {
    const data = await getRunStatus(runId);
    if (data) setStatus(data);
  };

  const connectSSE = () => {
    if (esRef.current) esRef.current.close();
    const es = new EventSource(`http://localhost:8090/events/run-progress?run_id=${runId}`);
    esRef.current = es;
    setSseConnected(true);
    es.addEventListener('run.progress', (e: MessageEvent) => {
      try {
        const rec = JSON.parse(e.data);
        setStatus(rec);
        if (rec.done) {
          es.close();
          setSseConnected(false);
        }
      } catch {}
    });
    es.onerror = () => {
      setSseConnected(false);
      es.close();
    };
  };

  useEffect(() => {
    loadStatus();
    return () => { esRef.current?.close(); };
  }, [runId]);

  if (!status) return null;

  const stage = status.stage ?? 'NOT_STARTED';
  const pct = status.pct ?? 0;
  const done = status.done ?? false;

  return (
    <div className="mt-4 p-4 border rounded-lg bg-muted/30" data-testid="run-live-ready">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">Live Run Progress</span>
        <div className="flex items-center gap-2">
          {sseConnected && (
            <Badge className="bg-green-500 text-white text-xs">● Live</Badge>
          )}
          <Button size="sm" variant="outline" onClick={connectSSE} data-testid="run-live-connect">
            Start Live
          </Button>
        </div>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span data-testid="run-live-stage">{STAGE_LABELS[stage] ?? stage}</span>
          <span data-testid="run-live-pct">{pct}%</span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${done ? 'bg-green-500' : 'bg-primary'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        {done && (
          <p className="text-xs text-green-600 font-medium" data-testid="run-live-done">
            ✓ Run complete
          </p>
        )}
      </div>
    </div>
  );
}

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
      // Backend returns array directly, not { runs: [] }
      setRuns(Array.isArray(result) ? result : result.runs || []);
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
                  <th className="text-center p-2">Provenance</th>
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
                      <td className="text-center p-2" onClick={(e) => e.stopPropagation()}>
                        <ProvenanceDrawer kind="run" resourceId={run.run_id} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </Card>
      {selectedRuns.length === 1 && (
        <LiveRunPanel runId={selectedRuns[0]} />
      )}
    </div>
  );
}
