import { useState, useCallback } from 'react';
import {
  postReplayStore,
  postReplayVerify,
  getReplaySuites,
  postReplayRunSuite,
  exportReproPack,
} from '../lib/api';

export default function ReplayPage() {
  const [suites, setSuites] = useState<any[]>([]);
  const [suitesReady, setSuitesReady] = useState(false);
  const [selectedSuite, setSelectedSuite] = useState<string>('suite_market_data_v1');
  const [scorecard, setScorecard] = useState<any>(null);
  const [scorecardReady, setScorecardReady] = useState(false);
  const [reproReport, setReproReport] = useState<any>(null);
  const [storeResult, setStoreResult] = useState<any>(null);
  const [verifyResult, setVerifyResult] = useState<any>(null);
  const [replayId, setReplayId] = useState('');
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'suites' | 'store' | 'repro'>('suites');

  const loadSuites = useCallback(async () => {
    setLoading(true);
    const result = await getReplaySuites();
    if (result?.suites) {
      setSuites(result.suites);
      setSuitesReady(true);
    }
    setLoading(false);
  }, []);

  const runSuite = useCallback(async () => {
    if (!selectedSuite) return;
    setLoading(true);
    setScorecardReady(false);
    const result = await postReplayRunSuite(selectedSuite);
    if (result?.suite_id) {
      setScorecard(result);
      setScorecardReady(true);
    }
    setLoading(false);
  }, [selectedSuite]);

  const handleStoreDemo = useCallback(async () => {
    setLoading(true);
    const result = await postReplayStore({
      endpoint: '/market/spot',
      request_payload: { symbol: 'AAPL' },
      response_payload: { symbol: 'AAPL', price: 150.0, output_hash: 'abc123' },
    });
    if (result?.replay_id) {
      setStoreResult(result);
      setReplayId(result.replay_id);
    }
    setLoading(false);
  }, []);

  const handleVerify = useCallback(async () => {
    if (!replayId.trim()) return;
    setLoading(true);
    const result = await postReplayVerify(replayId.trim());
    setVerifyResult(result);
    setLoading(false);
  }, [replayId]);

  const handleExportRepro = useCallback(async () => {
    if (!scorecard) return;
    setLoading(true);
    const result = await exportReproPack(scorecard.suite_id);
    setReproReport(result);
    setLoading(false);
  }, [scorecard]);

  return (
    <div data-testid="replay-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Replay & Reproducibility</h1>
      <p className="text-gray-500 text-sm mb-6">
        Store run outputs, verify hashes for tamper detection, and run golden suites for reproducibility.
      </p>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b">
        {(['suites', 'store', 'repro'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium ${tab === t ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            data-testid={`replay-tab-${t}`}
          >
            {t === 'suites' ? 'Golden Suites' : t === 'store' ? 'Store & Verify' : 'Repro Report'}
          </button>
        ))}
      </div>

      {/* Golden Suites tab */}
      {tab === 'suites' && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <button
              onClick={loadSuites}
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50 mr-2"
              data-testid="replay-load-suites-btn"
            >
              {loading ? 'Loading…' : 'Load Suites'}
            </button>
          </div>

          {suitesReady && (
            <div className="bg-white border rounded-lg p-4" data-testid="replay-suites-ready">
              <h3 className="text-sm font-semibold mb-3">Available Suites</h3>
              <div className="space-y-2">
                {suites.map(s => (
                  <div
                    key={s.suite_id}
                    className={`border rounded p-3 cursor-pointer ${selectedSuite === s.suite_id ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'}`}
                    onClick={() => setSelectedSuite(s.suite_id)}
                    data-testid={`replay-suite-${s.suite_id}`}
                  >
                    <p className="text-sm font-medium">{s.name}</p>
                    <p className="text-xs text-gray-500">{s.description} · {s.case_count} cases</p>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <button
                  onClick={runSuite}
                  disabled={!selectedSuite || loading}
                  className="bg-green-600 text-white px-4 py-1.5 rounded text-sm hover:bg-green-700 disabled:opacity-50"
                  data-testid="replay-run-suite-btn"
                >
                  Run Suite
                </button>
              </div>
            </div>
          )}

          {scorecardReady && scorecard && (
            <div className="bg-white border rounded-lg p-4" data-testid="replay-scorecard-ready">
              <h3 className="text-sm font-semibold mb-3">Scorecard: {scorecard.suite_name}</h3>
              <div className="grid grid-cols-4 gap-4 mb-4 text-sm">
                <div>
                  <p className="text-xs text-gray-500">Total</p>
                  <p className="font-bold">{scorecard.total}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Passed</p>
                  <p className="font-bold text-green-600">{scorecard.passed}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Failed</p>
                  <p className={`font-bold ${scorecard.failed > 0 ? 'text-red-600' : 'text-gray-400'}`}>{scorecard.failed}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Pass Rate</p>
                  <p className="font-bold text-green-600">{scorecard.pass_rate}%</p>
                </div>
              </div>
              <p className="text-xs text-gray-400">Hash: {scorecard.output_hash}</p>
              <button
                onClick={handleExportRepro}
                className="mt-3 border border-blue-600 text-blue-600 px-4 py-1.5 rounded text-sm hover:bg-blue-50"
                data-testid="replay-export-repro-btn"
              >
                Export Repro Report
              </button>
            </div>
          )}
        </div>
      )}

      {/* Store & Verify tab */}
      {tab === 'store' && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-sm font-semibold mb-3">Store Demo Entry</h3>
            <button
              onClick={handleStoreDemo}
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              data-testid="replay-store-btn"
            >
              {loading ? 'Storing…' : 'Store Demo Entry'}
            </button>
            {storeResult && (
              <div className="mt-3 bg-green-50 border border-green-200 rounded p-3" data-testid="replay-stored">
                <p className="text-xs text-green-700">✓ Stored</p>
                <p className="font-mono text-xs">{storeResult.replay_id}</p>
              </div>
            )}
          </div>

          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-sm font-semibold mb-3">Verify Entry</h3>
            <input
              className="border rounded px-3 py-1.5 text-xs font-mono w-full mb-3"
              placeholder="Replay ID..."
              value={replayId}
              onChange={e => setReplayId(e.target.value)}
              data-testid="replay-id-input"
            />
            <button
              onClick={handleVerify}
              disabled={!replayId.trim() || loading}
              className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              data-testid="replay-verify-btn"
            >
              Verify
            </button>
            {verifyResult && (
              <div
                className={`mt-3 border rounded p-3 ${verifyResult.verified ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}
                data-testid="replay-verify-result"
              >
                <p className={`text-xs font-medium ${verifyResult.verified ? 'text-green-700' : 'text-red-700'}`}>
                  {verifyResult.verified ? '✓ Verified' : `✗ Not verified (${verifyResult.mismatch_count} mismatch)`}
                </p>
                <p className="font-mono text-xs text-gray-500 mt-1">
                  Hash: {verifyResult.response_hash}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Repro Report tab */}
      {tab === 'repro' && (
        <div className="space-y-4">
          {reproReport ? (
            <div className="bg-white border rounded-lg p-4" data-testid="repro-report-ready">
              <h3 className="text-sm font-semibold mb-3">Reproducibility Report</h3>
              <div className="grid grid-cols-3 gap-4 text-sm mb-4">
                <div>
                  <p className="text-xs text-gray-500">Suite</p>
                  <p className="font-medium">{reproReport.scorecard?.suite_id}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Pass Rate</p>
                  <p className="font-bold text-green-600">{reproReport.scorecard?.pass_rate}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Manifest Hash</p>
                  <p className="font-mono text-xs">{reproReport.manifest?.manifest_hash}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 border rounded-lg p-6 text-center text-gray-400 text-sm">
              Run a suite in the Golden Suites tab, then export the repro report.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
