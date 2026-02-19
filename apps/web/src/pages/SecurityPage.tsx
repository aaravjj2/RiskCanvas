import { useState, useCallback, useEffect } from 'react';
import { getSecurityRules, scanDiff, getSbom, exportDevSecOpsPack, getAttestation } from '@/lib/api';

const DEMO_DIFF = `+API_KEY = 'sk-abc123def456ghi789jkl012mno34'
+PASSWORD = 'super_secret_pass_999'
+DATABASE_URL = 'postgresql://admin:insecure_pw123@localhost:5432/riskcanvas'
`;

export default function SecurityPage() {
  const [rules, setRules] = useState<any[]>([]);
  const [scanResult, setScanResult] = useState<any>(null);
  const [sbom, setSbom] = useState<any>(null);
  const [attestation, setAttestation] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [diffContent, setDiffContent] = useState(DEMO_DIFF);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRules = useCallback(async () => {
    const data = await getSecurityRules();
    if (data) setRules(data.rules ?? []);
  }, []);

  useEffect(() => { loadRules(); }, [loadRules]);

  const runScan = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await scanDiff(diffContent); if (data) setScanResult(data); }
    catch { setError('Scan failed'); }
    setLoading(false);
  }, [diffContent]);

  const loadSbom = useCallback(async () => {
    setLoading(true);
    try { const data = await getSbom(); if (data) setSbom(data); }
    catch { setError('SBOM fetch failed'); }
    setLoading(false);
  }, []);

  const loadAttestation = useCallback(async () => {
    if (!scanResult) return;
    setLoading(true);
    const data = await getAttestation('HEAD', 'proof_pack_demo_001', scanResult);
    if (data) setAttestation(data);
    setLoading(false);
  }, [scanResult]);

  const doExport = useCallback(async () => {
    setLoading(true);
    const data = await exportDevSecOpsPack('HEAD', 'proof_pack_demo_001', diffContent);
    if (data) setExportResult(data);
    setLoading(false);
  }, [diffContent]);

  const sc = (sev: string) => sev === 'CRITICAL' ? 'text-red-700 bg-red-50' : sev === 'HIGH' ? 'text-orange-700 bg-orange-50' : 'text-yellow-700 bg-yellow-50';

  return (
    <div data-testid="sec-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">DevSecOps Pack</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 25   v4.48–v4.49</p>
      {error && <div data-testid="sec-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Secret Scanner</h2>
        <textarea data-testid="sec-diff-input" value={diffContent} onChange={e => setDiffContent(e.target.value)} rows={5} className="w-full border rounded px-3 py-2 text-xs font-mono mb-3" />
        <div className="flex gap-2">
          <button data-testid="sec-scan-btn" onClick={runScan} disabled={loading} className="px-3 py-1 bg-red-600 text-white rounded text-sm disabled:opacity-50">Scan for Secrets</button>
          <button data-testid="sec-sbom-btn" onClick={loadSbom} disabled={loading} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">Get SBOM</button>
          <button data-testid="sec-attest-btn" onClick={loadAttestation} disabled={loading || !scanResult} className="px-3 py-1 bg-purple-600 text-white rounded text-sm disabled:opacity-50">Build Attestation</button>
          <button data-testid="sec-export-btn" onClick={doExport} disabled={loading} className="px-3 py-1 bg-gray-700 text-white rounded text-sm disabled:opacity-50">Export DevSecOps Pack</button>
        </div>
      </section>
      {scanResult && (
        <div data-testid="sec-results-ready" className="mb-6 bg-gray-50 rounded p-4 text-sm">
          <div className="flex items-center gap-3 mb-3">
            <span className="font-semibold">Status:</span>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${scanResult.status === 'BLOCKED' ? 'bg-red-100 text-red-700' : scanResult.status === 'WARNINGS' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>{scanResult.status}</span>
            <span className="text-xs text-gray-500">{scanResult.total_findings} finding(s)   {scanResult.blocker_count} blocker(s)</span>
          </div>
          <div className="space-y-2">
            {scanResult.findings?.map((f: any, i: number) => (
              <div key={i} className={`p-2 rounded text-xs ${sc(f.severity)}`}>
                <span className="font-semibold">[{f.rule_id}]</span> {f.rule_name} - Line {f.line_no}
                <div className="mt-0.5">→ {f.remediation}</div>
              </div>
            ))}
          </div>
          <div className="font-mono text-xs text-gray-400 mt-2">hash: {scanResult.output_hash?.slice(0,16)}...</div>
        </div>
      )}
      {sbom && (
        <div data-testid="sec-sbom-ready" className="mb-6 bg-gray-50 rounded p-4 text-sm">
          <div className="font-semibold mb-2">SBOM - {sbom.total_packages} packages</div>
          <div className="font-mono text-xs text-gray-400">sbom_hash: {sbom.sbom_hash?.slice(0,16)}...</div>
        </div>
      )}
      {attestation && (
        <div data-testid="sec-attest-ready" className="mb-6 bg-gray-50 rounded p-4 text-sm">
          <div className="font-semibold mb-1">Attestation</div>
          <div>Commit: {attestation.commit_sha}   Status: <span className={attestation.scan_status === 'BLOCKED' ? 'text-red-600' : 'text-green-600'}>{attestation.scan_status}</span></div>
          <div className="font-mono text-xs text-gray-400 mt-1">attestation_hash: {attestation.attestation_hash?.slice(0,16)}...</div>
        </div>
      )}
      {rules.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-2">Active Rules ({rules.length})</h2>
          <table className="w-full text-xs">
            <thead><tr className="border-b"><th className="text-left py-1">Rule</th><th className="text-left py-1">Name</th><th className="text-left py-1">Severity</th></tr></thead>
            <tbody>
              {rules.map((r: any) => (
                <tr key={r.rule_id} data-testid={`sec-rule-${r.rule_id}`} className="border-b border-gray-100">
                  <td className="py-1 font-mono">{r.rule_id}</td>
                  <td className="py-1">{r.name}</td>
                  <td className={`py-1 ${r.severity === 'CRITICAL' ? 'text-red-600' : r.severity === 'HIGH' ? 'text-orange-600' : 'text-gray-600'}`}>{r.severity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
      {exportResult && <div data-testid="sec-export-ready" className="mt-4 bg-gray-50 rounded p-3 text-xs font-mono">pack_hash: {exportResult.pack_hash?.slice(0,16)}...</div>}
    </div>
  );
}
