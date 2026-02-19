import { useState, useCallback, useEffect } from 'react';
import { listMrs, getMrDiff, postMrComment, exportMrCompliancePack } from '@/lib/api';

export default function GitLabPage() {
  const [mrs, setMrs] = useState<any[]>([]);
  const [selectedIid, setSelectedIid] = useState<number | null>(null);
  const [diffData, setDiffData] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [commentText, setCommentText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMrs = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await listMrs(); if (data) setMrs(data.merge_requests ?? data.mrs ?? []); }
    catch { setError('Failed to load MRs'); }
    setLoading(false);
  }, []);

  useEffect(() => { loadMrs(); }, [loadMrs]);

  const loadDiff = useCallback(async (iid: number) => {
    setLoading(true); setSelectedIid(iid); setDiffData(null);
    try { const data = await getMrDiff(iid); if (data) setDiffData(data); }
    catch { setError('Failed to load diff'); }
    setLoading(false);
  }, []);

  const handleComment = useCallback(async () => {
    if (!selectedIid || !commentText.trim()) return;
    setLoading(true);
    await postMrComment(selectedIid, commentText.trim(), 'demo_user');
    setCommentText('');
    setLoading(false);
  }, [selectedIid, commentText]);

  const doExport = useCallback(async () => {
    if (!selectedIid) return;
    setLoading(true);
    const data = await exportMrCompliancePack(selectedIid);
    if (data) setExportResult(data);
    setLoading(false);
  }, [selectedIid]);

  const sc = (s: string) => s === 'opened' ? 'text-green-600' : s === 'merged' ? 'text-blue-600' : 'text-gray-500';

  return (
    <div data-testid="gitlab-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">GitLab MR Compliance</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 23   v4.42–v4.45   Offline fixtures</p>
      {error && <div data-testid="gitlab-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      <button data-testid="gitlab-refresh-btn" onClick={loadMrs} disabled={loading} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50 mb-4">Refresh MRs</button>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h2 className="text-lg font-semibold mb-2">Merge Requests</h2>
          {mrs.length > 0 && (
            <div data-testid="gitlab-mr-list-ready" className="space-y-2">
              {mrs.map((mr: any) => (
                <div key={mr.iid} data-testid={`gitlab-mr-row-${mr.iid}`} onClick={() => loadDiff(mr.iid)}
                  className={`p-3 rounded border cursor-pointer text-sm ${selectedIid === mr.iid ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'}`}>
                  <div className="font-medium">!{mr.iid} - {mr.title}</div>
                  <div className="text-xs mt-1"><span className={sc(mr.state)}>{mr.state}</span>   {mr.source_branch}</div>
                  {mr.policy_flags?.length > 0 && <div className="text-xs text-red-600 mt-1">⚠ {mr.policy_flags.join(', ')}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-2">Diff</h2>
          {diffData && (
            <div data-testid="gitlab-diff-ready" className="bg-gray-50 rounded p-4 text-sm space-y-3">
              <div className="font-medium">!{diffData.iid} - {diffData.title}</div>
              <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-40 overflow-y-auto whitespace-pre-wrap">{diffData.diff?.slice(0, 500)}</pre>
              <div className="font-mono text-xs text-gray-400">hash: {diffData.diff_hash?.slice(0, 16)}...</div>
              <input data-testid="gitlab-comment-input" value={commentText} onChange={e => setCommentText(e.target.value)} placeholder="Add a comment..." className="border rounded px-2 py-1 text-sm w-full" />
              <div className="flex gap-2">
                <button data-testid="gitlab-comment-btn" onClick={handleComment} disabled={loading || !commentText.trim()} className="px-2 py-1 bg-blue-600 text-white rounded text-xs disabled:opacity-50">Post Comment</button>
                <button data-testid="gitlab-export-btn" onClick={doExport} disabled={loading} className="px-2 py-1 bg-gray-700 text-white rounded text-xs disabled:opacity-50">Export Compliance Pack</button>
              </div>
            </div>
          )}
          {exportResult && <div data-testid="gitlab-export-ready" className="mt-2 bg-gray-50 rounded p-3 text-xs font-mono">pack_hash: {exportResult.pack_hash?.slice(0,16)}...</div>}
        </div>
      </div>
    </div>
  );
}
