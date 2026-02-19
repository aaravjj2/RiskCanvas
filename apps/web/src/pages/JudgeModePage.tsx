import { useState, useCallback } from 'react';
import { judgeW26W32GeneratePack, judgeW26W32GetFiles } from '@/lib/api';

export default function JudgeModePage() {
  const [pack, setPack] = useState<any>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doGenerate = useCallback(async () => {
    setLoading(true); setError(null); setPack(null); setFiles([]);
    try {
      const data = await judgeW26W32GeneratePack();
      if (data) setPack(data);
    } catch { setError('Pack generation failed'); }
    setLoading(false);
  }, []);

  const doGetFiles = useCallback(async () => {
    setLoading(true);
    const data = await judgeW26W32GetFiles();
    if (data) setFiles(data.files ?? []);
    setLoading(false);
  }, []);

  const verdictStyle = (v: string) =>
    v === 'PASS' ? 'text-green-700 bg-green-100 border-green-300' : 'text-red-700 bg-red-100 border-red-300';

  return (
    <div data-testid="judge-mode-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Judge Mode — Wave 26-32</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 32 · v4.72–v4.73 · Submission Pack Generator</p>

      {error && <div data-testid="judge-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-3">Generate Submission Pack</h2>
        <p className="text-sm text-gray-600 mb-4">
          Sweeps all Wave 26–32 modules, evaluates evidence, and exports a judge-readable pack
          with summary, gate scores, wave evidence, and audit chain.
        </p>
        <div className="flex gap-2">
          <button data-testid="judge-generate-btn" onClick={doGenerate} disabled={loading}
            className="px-4 py-2 bg-gray-900 text-white rounded text-sm disabled:opacity-50">
            Generate Pack
          </button>
          <button data-testid="judge-files-btn" onClick={doGetFiles} disabled={loading}
            className="px-4 py-2 bg-gray-600 text-white rounded text-sm disabled:opacity-50">
            List Files
          </button>
        </div>
      </section>

      {pack && (
        <div data-testid="judge-pack-ready" className="mb-6">
          <div className={`inline-flex items-center gap-3 px-4 py-3 rounded-lg border mb-4 ${verdictStyle(pack.summary?.verdict)}`}>
            <span className="text-xl font-bold">{pack.summary?.verdict}</span>
            <span className="text-lg font-semibold">{pack.summary?.score_pct}%</span>
            <span className="text-sm">{pack.summary?.waves_evaluated} waves · {pack.summary?.total_releases} releases</span>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-gray-50 rounded p-3 text-sm">
              <div className="font-semibold mb-1">Version Range</div>
              <div className="font-mono text-xs">{pack.summary?.version_range}</div>
            </div>
            <div className="bg-gray-50 rounded p-3 text-sm">
              <div className="font-semibold mb-1">Pack Hash</div>
              <div className="font-mono text-xs">{pack.pack_hash?.slice(0, 24)}…</div>
            </div>
          </div>

          <div className="bg-gray-50 rounded p-4 mb-4 text-sm">
            <div className="font-semibold mb-2">Modules ({pack.summary?.modules?.length})</div>
            <div className="flex gap-2 flex-wrap">
              {pack.summary?.modules?.map((m: string) => (
                <span key={m} className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded font-mono">{m}</span>
              ))}
            </div>
          </div>

          <div className="font-mono text-xs text-gray-400">
            audit_chain_head: {pack.audit_chain_head_hash?.slice(0, 24)}…
          </div>
        </div>
      )}

      {files.length > 0 && (
        <div data-testid="judge-files-ready" className="mb-6">
          <h3 className="font-semibold text-sm mb-2">Pack Files ({files.length})</h3>
          <div className="space-y-2">
            {files.map((f: any) => (
              <div key={f.name} data-testid={`judge-file-${f.name.replace('.', '-')}`}
                className="bg-gray-50 rounded p-3 text-sm">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono font-semibold text-gray-700">{f.name}</span>
                  <span className="text-xs text-gray-400">{f.content?.length} bytes</span>
                </div>
                <pre className="text-xs text-gray-500 font-mono overflow-x-auto max-h-32 overflow-y-auto">
                  {f.content?.slice(0, 300)}{f.content?.length > 300 ? '…' : ''}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
