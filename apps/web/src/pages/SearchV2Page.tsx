import { useState, useCallback, useEffect } from 'react';
import { searchV2Stats, searchV2Query } from '@/lib/api';

const TYPE_OPTIONS = ['', 'mr_review', 'pipeline', 'incident_drill', 'workflow', 'policy_v2', 'risk_model'];

export default function SearchV2Page() {
  const [stats, setStats] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    const data = await searchV2Stats();
    if (data) setStats(data);
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);

  const doSearch = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await searchV2Query(query, typeFilter || undefined, 1, 20);
      if (data) setResults(data);
    } catch { setError('Search failed'); }
    setLoading(false);
  }, [query, typeFilter]);

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') doSearch();
  };

  const typeColors: Record<string, string> = {
    mr_review: 'text-purple-700 bg-purple-100',
    pipeline: 'text-blue-700 bg-blue-100',
    incident_drill: 'text-red-700 bg-red-100',
    workflow: 'text-green-700 bg-green-100',
    policy_v2: 'text-orange-700 bg-orange-100',
    risk_model: 'text-gray-700 bg-gray-100',
  };

  return (
    <div data-testid="search-v2-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Search V2</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 31 · v4.70–v4.71 · Unified Search</p>

      {error && <div data-testid="sv2-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="mb-6">
        <div className="flex gap-2 mb-3">
          <input
            data-testid="sv2-query-input"
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Search across all document types…"
            className="flex-1 border rounded px-3 py-2 text-sm"
          />
          <select data-testid="sv2-type-filter" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}
            className="border rounded px-2 py-2 text-sm">
            {TYPE_OPTIONS.map(t => (
              <option key={t} value={t}>{t || 'All types'}</option>
            ))}
          </select>
          <button data-testid="sv2-search-btn" onClick={doSearch} disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm disabled:opacity-50">
            Search
          </button>
        </div>
      </section>

      {stats && (
        <div data-testid="sv2-stats-ready" className="mb-4 bg-gray-50 rounded p-3 text-sm">
          <div className="font-semibold mb-2">{stats.total_docs} documents indexed</div>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(stats.by_type ?? {}).map(([type, count]: [string, any]) => (
              <span key={type} className={`px-2 py-0.5 rounded text-xs font-semibold ${typeColors[type] ?? 'bg-gray-100 text-gray-600'}`}>
                {type}: {count}
              </span>
            ))}
          </div>
          <div className="font-mono text-xs text-gray-400 mt-2">index_hash: {stats.index_hash?.slice(0, 16)}…</div>
        </div>
      )}

      {results && (
        <div data-testid="sv2-results-ready" className="mb-4">
          <div className="text-sm text-gray-500 mb-3">
            {results.total} result(s) for "{results.query}" {results.type_filter ? `[${results.type_filter}]` : ''}
          </div>
          <div className="space-y-2">
            {results.results?.map((doc: any, i: number) => (
              <div key={doc.id || i} data-testid={`sv2-result-${i}`} className="bg-gray-50 rounded p-3 text-sm">
                <div className="flex items-start gap-2">
                  <span className={`shrink-0 px-1.5 py-0.5 rounded text-xs font-semibold ${typeColors[doc.type] ?? 'bg-gray-100 text-gray-600'}`}>
                    {doc.type}
                  </span>
                  <div>
                    <div className="font-semibold">{doc.title}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{doc.body?.slice(0, 100)}…</div>
                    <div className="flex gap-1 mt-1">
                      {doc.tags?.map((tag: string) => (
                        <span key={tag} className="text-xs text-gray-400 bg-gray-100 px-1 py-0.5 rounded">{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
