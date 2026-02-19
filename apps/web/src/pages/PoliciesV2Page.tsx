import { useState, useCallback, useEffect } from 'react';
import { policyV2Create, policyV2Publish, policyV2Rollback, policyV2List, policyV2Versions } from '@/lib/api';

export default function PoliciesV2Page() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [versions, setVersions] = useState<any[]>([]);
  const [selectedSlug, setSelectedSlug] = useState('');
  const [lastCreated, setLastCreated] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPolicies = useCallback(async () => {
    const data = await policyV2List();
    if (data) setPolicies(data.policies ?? []);
  }, []);

  useEffect(() => { loadPolicies(); }, [loadPolicies]);

  const doCreate = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await policyV2Create(
        'risk-assessment-policy',
        'Risk Assessment Policy',
        'All positions must be assessed for market, credit, and operational risk daily.',
        ['risk', 'compliance'],
      );
      if (data) { setLastCreated(data); await loadPolicies(); }
    } catch { setError('Create failed'); }
    setLoading(false);
  }, [loadPolicies]);

  const doPublish = useCallback(async () => {
    const slug = selectedSlug || lastCreated?.slug;
    if (!slug) return;
    setLoading(true);
    const data = await policyV2Publish(slug, null);
    if (data) { setLastCreated(data); await loadPolicies(); }
    setLoading(false);
  }, [selectedSlug, lastCreated, loadPolicies]);

  const doRollback = useCallback(async () => {
    const slug = selectedSlug || lastCreated?.slug;
    if (!slug || (lastCreated?.version_number ?? 1) < 2) return;
    setLoading(true);
    const data = await policyV2Rollback(slug, 1);
    if (data) { setLastCreated(data); await loadPolicies(); }
    setLoading(false);
  }, [selectedSlug, lastCreated, loadPolicies]);

  const doLoadVersions = useCallback(async () => {
    const slug = selectedSlug || lastCreated?.slug;
    if (!slug) return;
    setLoading(true);
    const data = await policyV2Versions(slug);
    if (data) setVersions(data.versions ?? []);
    setLoading(false);
  }, [selectedSlug, lastCreated]);

  const statusColor = (s: string) =>
    s === 'published' ? 'text-green-700 bg-green-100' :
    s === 'rolled_back' ? 'text-gray-500 bg-gray-100' :
    'text-yellow-700 bg-yellow-100';

  return (
    <div data-testid="policies-v2-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Policy Registry V2</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 30 · v4.66–v4.69 · Versioned Policies</p>

      {error && <div data-testid="pv2-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-3">Policy Actions</h2>
        <div className="flex gap-2 flex-wrap">
          <button data-testid="pv2-create-btn" onClick={doCreate} disabled={loading}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">
            Create Policy
          </button>
          <button data-testid="pv2-publish-btn" onClick={doPublish} disabled={loading || (!lastCreated && !selectedSlug)}
            className="px-3 py-1 bg-green-600 text-white rounded text-sm disabled:opacity-50">
            Publish
          </button>
          <button data-testid="pv2-rollback-btn" onClick={doRollback} disabled={loading || (!lastCreated && !selectedSlug)}
            className="px-3 py-1 bg-orange-600 text-white rounded text-sm disabled:opacity-50">
            Rollback to v1
          </button>
          <button data-testid="pv2-versions-btn" onClick={doLoadVersions} disabled={loading || (!lastCreated && !selectedSlug)}
            className="px-3 py-1 bg-purple-600 text-white rounded text-sm disabled:opacity-50">
            Load Versions
          </button>
        </div>
      </section>

      {lastCreated && (
        <div data-testid="pv2-created-ready" className="mb-4 bg-gray-50 rounded p-4 text-sm">
          <div className="flex items-center gap-3 mb-2">
            <span className="font-semibold">{lastCreated.title}</span>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${statusColor(lastCreated.status)}`}>{lastCreated.status}</span>
            <span className="text-xs text-gray-500">v{lastCreated.version_number}</span>
          </div>
          <div className="text-xs text-gray-600 mb-1">{lastCreated.body?.slice(0, 100)}…</div>
          <div className="font-mono text-xs text-gray-400">hash: {lastCreated.content_hash?.slice(0, 16)}…</div>
          <div className="font-mono text-xs text-gray-400">chain: {lastCreated.audit_chain_hash?.slice(0, 16)}…</div>
        </div>
      )}

      {versions.length > 0 && (
        <div data-testid="pv2-versions-ready" className="mb-4">
          <h3 className="font-semibold text-sm mb-2">Version History ({versions.length})</h3>
          <table className="w-full text-xs">
            <thead><tr className="border-b"><th className="text-left py-1">v</th><th className="text-left py-1">Status</th><th className="text-left py-1">Hash</th></tr></thead>
            <tbody>
              {versions.map((v: any) => (
                <tr key={v.version_number} data-testid={`pv2-ver-${v.version_number}`} className="border-b border-gray-100">
                  <td className="py-1 font-mono">v{v.version_number}</td>
                  <td className="py-1"><span className={`px-1.5 py-0.5 rounded text-xs ${statusColor(v.status)}`}>{v.status}</span></td>
                  <td className="py-1 font-mono text-gray-400">{v.content_hash?.slice(0, 12)}…</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {policies.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-semibold mb-2">All Policies ({policies.length})</h2>
          <table className="w-full text-xs">
            <thead><tr className="border-b"><th className="text-left py-1">Slug</th><th className="text-left py-1">Title</th><th className="text-left py-1">Latest</th><th className="text-left py-1">Status</th></tr></thead>
            <tbody>
              {policies.map((p: any) => (
                <tr key={p.slug} data-testid={`pv2-row-${p.slug}`} className="border-b border-gray-100 cursor-pointer hover:bg-gray-50"
                  onClick={() => setSelectedSlug(p.slug)}>
                  <td className="py-1 font-mono">{p.slug}</td>
                  <td className="py-1">{p.title}</td>
                  <td className="py-1">v{p.latest_version}</td>
                  <td className="py-1"><span className={`px-1.5 py-0.5 rounded text-xs ${statusColor(p.status)}`}>{p.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
