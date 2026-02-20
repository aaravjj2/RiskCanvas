import { useState, useCallback } from 'react';
import { judgeW26W32GeneratePack, judgeW26W32GetFiles, judgeV4Generate, judgeV4ListPacks } from '@/lib/api';

// ── Launch Rail helpers ────────────────────────────────────────────────────────
const DEPLOY_TARGETS = [
  {
    id: 'azure',
    label: 'Azure (Microsoft)',
    color: 'bg-blue-600 hover:bg-blue-700',
    testid: 'launch-azure',
    url: 'https://portal.azure.com/#create/hub',
  },
  {
    id: 'gitlab',
    label: 'GitLab CI/CD',
    color: 'bg-orange-600 hover:bg-orange-700',
    testid: 'launch-gitlab',
    url: 'https://gitlab.com/projects/new',
  },
  {
    id: 'digitalocean',
    label: 'DigitalOcean',
    color: 'bg-teal-600 hover:bg-teal-700',
    testid: 'launch-digitalocean',
    url: 'https://cloud.digitalocean.com/apps/new',
  },
] as const;

export default function JudgeModePage() {
  const [pack, setPack] = useState<any>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Wave 71 — v4 state
  const [v4Pack, setV4Pack] = useState<any>(null);
  const [v4Packs, setV4Packs] = useState<any[]>([]);
  const [v4Loading, setV4Loading] = useState(false);
  const [v4Error, setV4Error] = useState<string | null>(null);
  const [launchTarget, setLaunchTarget] = useState<string | null>(null);

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

  const doV4Generate = useCallback(async () => {
    setV4Loading(true); setV4Error(null); setV4Pack(null);
    try {
      const data = await judgeV4Generate();
      if (data) setV4Pack(data);
    } catch { setV4Error('v4 pack generation failed'); }
    setV4Loading(false);
  }, []);

  const doV4ListPacks = useCallback(async () => {
    setV4Loading(true);
    try {
      const data = await judgeV4ListPacks();
      if (data) setV4Packs(data.packs ?? []);
    } catch { /* ignore */ }
    setV4Loading(false);
  }, []);

  const doLaunch = useCallback((targetId: string, url: string) => {
    setLaunchTarget(targetId);
    window.open(url, '_blank', 'noreferrer');
  }, []);

  const gradeColor = (g: string) => {
    if (g === 'A') return 'text-green-700 bg-green-100 border-green-300';
    if (g === 'B') return 'text-blue-700 bg-blue-100 border-blue-300';
    if (g === 'C') return 'text-yellow-700 bg-yellow-100 border-yellow-300';
    return 'text-red-700 bg-red-100 border-red-300';
  };

  const verdictStyle = (v: string) =>
    v === 'PASS' ? 'text-green-700 bg-green-100 border-green-300' : 'text-red-700 bg-red-100 border-red-300';

  return (
    <div data-testid="judge-mode-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Judge Mode</h1>
      <p className="text-gray-500 mb-6 text-sm">v5.61.0 · Wave 26–72 · Submission Pack Generator</p>

      {error && <div data-testid="judge-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      {/* ── Wave 71: Judge Mode v4 ────────────────────────────────────────── */}
      <section data-testid="judge-v4-section" className="mb-8 border border-gray-200 rounded-lg p-5">
        <h2 className="text-lg font-semibold mb-1">Judge Pack v4 — Wave 62–72</h2>
        <p className="text-sm text-gray-500 mb-4">
          Rubric: decision_support · compliance · deployment_readiness · scenario_coverage · review_quality
        </p>

        {v4Error && <div data-testid="judge-v4-error" className="mb-3 p-2 bg-red-50 text-red-700 rounded text-sm">{v4Error}</div>}

        <div className="flex gap-2 mb-4">
          <button data-testid="judge-v4-generate-btn" onClick={doV4Generate} disabled={v4Loading}
            className="px-4 py-2 bg-indigo-700 text-white rounded text-sm disabled:opacity-50 hover:bg-indigo-800">
            {v4Loading ? 'Generating…' : 'Generate v4 Pack'}
          </button>
          <button data-testid="judge-v4-list-btn" onClick={doV4ListPacks} disabled={v4Loading}
            className="px-4 py-2 bg-gray-600 text-white rounded text-sm disabled:opacity-50 hover:bg-gray-700">
            List Packs
          </button>
        </div>

        {v4Pack && (
          <div data-testid="judge-v4-pack-ready" className="mb-4">
            <div className={`inline-flex items-center gap-3 px-4 py-2 rounded-lg border mb-3 ${gradeColor(v4Pack.grade)}`}>
              <span data-testid="judge-v4-grade" className="text-2xl font-bold">{v4Pack.grade}</span>
              <span data-testid="judge-v4-score" className="text-lg font-semibold">
                {Number(v4Pack.final_score * 100).toFixed(1)}%
              </span>
              <span className="text-sm text-gray-500 font-mono">{v4Pack.pack_id?.slice(0, 16)}…</span>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-3">
              {v4Pack.sections?.map((s: any) => (
                <div key={s.section} data-testid={`judge-v4-section-${s.section}`}
                  className="bg-gray-50 rounded p-3 text-xs">
                  <div className="font-semibold text-gray-700 mb-1">{s.section}</div>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 bg-gray-200 rounded flex-1">
                      <div className="h-1.5 bg-indigo-500 rounded" style={{ width: `${s.score * 100}%` }} />
                    </div>
                    <span className="font-mono text-gray-500">{(s.score * 100).toFixed(0)}%</span>
                  </div>
                  {s.notes && <div className="text-gray-400 mt-1 truncate">{s.notes}</div>}
                </div>
              ))}
            </div>

            <div className="text-xs text-gray-400 font-mono">
              bundle: {v4Pack.bundle_size_bytes?.toLocaleString()} bytes · checksum: {v4Pack.bundle_checksum?.slice(0, 20)}…
            </div>
          </div>
        )}

        {v4Packs.length > 0 && (
          <div data-testid="judge-v4-packs-list" className="mb-4">
            <h3 className="text-sm font-semibold mb-2">Stored Packs ({v4Packs.length})</h3>
            <div className="space-y-1">
              {v4Packs.map((p: any) => (
                <div key={p.pack_id} data-testid={`judge-v4-pack-item`}
                  className="flex items-center gap-3 bg-gray-50 rounded px-3 py-2 text-xs">
                  <span className={`font-bold ${gradeColor(p.grade).split(' ')[0]}`}>{p.grade}</span>
                  <span className="font-mono text-gray-500">{p.pack_id?.slice(0, 20)}…</span>
                  <span className="text-gray-400">{(p.final_score * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Deploy Launch Rail ──────────────────────────────────────────── */}
        <div data-testid="judge-launch-rail" className="mt-4 pt-4 border-t border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Deploy Launch Rail</h3>
          <p className="text-xs text-gray-400 mb-3">
            One-click launch to cloud provider dashboards for deployment
          </p>
          <div className="flex gap-2 flex-wrap">
            {DEPLOY_TARGETS.map((t) => (
              <button
                key={t.id}
                data-testid={t.testid}
                onClick={() => doLaunch(t.id, t.url)}
                className={`px-4 py-2 text-white text-sm rounded font-medium ${t.color} transition-colors`}
              >
                {t.label}
                {launchTarget === t.id && <span className="ml-2 text-xs opacity-75">↗</span>}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── Wave 26-32: Legacy Pack ──────────────────────────────────────── */}
      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-3">Wave 26–32 Submission Pack</h2>
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
