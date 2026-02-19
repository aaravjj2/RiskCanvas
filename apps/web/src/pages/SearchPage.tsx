import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { searchQuery, searchReindex, searchStatus } from '@/lib/api';

const TYPE_LABELS: Record<string, string> = {
  run: 'Run',
  report: 'Report',
  audit: 'Audit',
  activity: 'Activity',
  policy: 'Policy',
  eval: 'Eval',
  sre_playbook: 'SRE Playbook',
};

const TYPE_COLORS: Record<string, string> = {
  run: 'bg-blue-100 text-blue-800',
  report: 'bg-green-100 text-green-800',
  audit: 'bg-gray-100 text-gray-700',
  activity: 'bg-purple-100 text-purple-800',
  policy: 'bg-yellow-100 text-yellow-800',
  eval: 'bg-orange-100 text-orange-800',
  sre_playbook: 'bg-red-100 text-red-800',
};

const ALL_FILTER_TYPES = Object.keys(TYPE_LABELS);

interface SearchResult {
  id: string;
  type: string;
  text: string;
  url: string;
  score: number;
}

export default function SearchPage({ initialQuery = '' }: { initialQuery?: string }) {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [grouped, setGrouped] = useState<Record<string, SearchResult[]>>({});
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [queryHash, setQueryHash] = useState('');
  const [highlightId, setHighlightId] = useState<string | null>(null);
  const [statusInfo, setStatusInfo] = useState<any>(null);
  const navigate = useNavigate();

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    const data = await searchQuery({
      text: query,
      filters: activeFilters.length > 0 ? activeFilters : undefined,
      limit: 20,
    });
    if (data) {
      setResults(data.results ?? []);
      setGrouped(data.grouped ?? {});
      setQueryHash(data.query_hash ?? '');
    }
    setLoading(false);
  };

  const handleReindex = async () => {
    setLoading(true);
    const data = await searchReindex();
    if (data) {
      const st = await searchStatus();
      setStatusInfo(st);
    }
    setLoading(false);
  };

  const handleResultClick = (result: SearchResult) => {
    setHighlightId(result.id);
    navigate(result.url);
  };

  const toggleFilter = (type: string) => {
    setActiveFilters(prev =>
      prev.includes(type) ? prev.filter(f => f !== type) : [...prev, type]
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSearch();
  };

  return (
    <div data-testid="search-page" className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Global Search</h1>
        <p className="text-muted-foreground">Search across runs, reports, audit, activity, policies, evals & playbooks</p>
      </div>

      {/* Search bar */}
      <div className="flex gap-2">
        <Input
          data-testid="search-input"
          placeholder="Search runs, reports, policies..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1"
        />
        <Button onClick={handleSearch} disabled={loading} data-testid="search-submit">
          Search
        </Button>
        <Button variant="outline" onClick={handleReindex} disabled={loading} data-testid="search-reindex">
          Reindex
        </Button>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2" data-testid="search-chips">
        {ALL_FILTER_TYPES.map(type => (
          <button
            key={type}
            onClick={() => toggleFilter(type)}
            data-testid={`search-chip-${type}`}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
              activeFilters.includes(type)
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-background border-border text-muted-foreground hover:border-primary'
            }`}
          >
            {TYPE_LABELS[type]}
          </button>
        ))}
      </div>

      {/* Status info */}
      {statusInfo && (
        <p className="text-xs text-muted-foreground font-mono">
          Index: {statusInfo.doc_count} docs   hash: {statusInfo.index_hash?.slice(0, 12)}
        </p>
      )}

      {/* Results */}
      {loading && <p className="text-muted-foreground text-sm">Searching...</p>}

      {!loading && results.length > 0 && (
        <div className="space-y-4" data-testid="search-results-ready">
          {queryHash && (
            <p className="text-xs text-muted-foreground font-mono">query_hash: {queryHash.slice(0, 16)}...</p>
          )}
          {/* Grouped by type */}
          {Object.entries(grouped).map(([type, items]) => (
            <div key={type} className="space-y-2">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                {TYPE_LABELS[type] ?? type} ({items.length})
              </h3>
              <div className="space-y-1">
                {items.map((item, idx) => (
                  <Card
                    key={item.id}
                    className={`p-3 cursor-pointer hover:shadow-md transition-shadow ${
                      highlightId === item.id ? 'ring-2 ring-primary' : ''
                    }`}
                    onClick={() => handleResultClick(item)}
                    data-testid={`search-result-${idx}`}
                    data-result-id={item.id}
                    data-result-type={item.type}
                    data-highlighted={highlightId === item.id ? 'true' : 'false'}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`text-xs px-2 py-0.5 rounded font-mono ${TYPE_COLORS[item.type] ?? 'bg-gray-100'}`}>
                        {item.type}
                      </span>
                      <span className="text-sm flex-1 truncate">{item.text}</span>
                      <Badge variant="outline" className="text-xs shrink-0">
                        {(item.score * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && results.length === 0 && query && (
        <p className="text-muted-foreground text-sm" data-testid="search-empty">
          No results for "{query}"
        </p>
      )}
    </div>
  );
}
