import { useState, useCallback, useEffect } from 'react';
import { listApprovals, createApproval, submitApproval, decideApproval, getApproval, exportApprovalPack } from '@/lib/api';

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await listApprovals(); if (data) setApprovals(data.approvals ?? []); }
    catch { setError('Failed to load approvals'); }
    setLoading(false);
  }, []);

  useEffect(() => { loadList(); }, [loadList]);

  const loadDetail = useCallback(async (id: string) => {
    setLoading(true); setSelectedId(id); setDetail(null);
    try { const data = await getApproval(id); if (data) setDetail(data); }
    catch { setError('Failed to load detail'); }
    setLoading(false);
  }, []);

  const handleCreate = useCallback(async () => {
    setLoading(true);
    await createApproval({ document_type: 'risk_limit_change', title: `Demo ${Date.now()}`, payload: { limit: 1e6 }, requester: 'demo_user' });
    await loadList();
    setLoading(false);
  }, [loadList]);

  const handleSubmit = useCallback(async (id: string) => {
    setLoading(true);
    await submitApproval(id, 'demo_user');
    await loadList();
    if (selectedId === id) await loadDetail(id);
    setLoading(false);
  }, [loadList, selectedId, loadDetail]);

  const handleDecide = useCallback(async (id: string, decision: 'approved' | 'rejected') => {
    setLoading(true);
    await decideApproval(id, decision, 'risk_committee');
    await loadList();
    if (selectedId === id) await loadDetail(id);
    setLoading(false);
  }, [loadList, selectedId, loadDetail]);

  const doExport = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    const data = await exportApprovalPack(selectedId);
    if (data) setExportResult(data);
    setLoading(false);
  }, [selectedId]);

  const sc = (s: string) => s === 'APPROVED' ? 'text-green-600' : s === 'REJECTED' ? 'text-red-600' : s === 'SUBMITTED' ? 'text-blue-600' : 'text-gray-500';

  return (
    <div data-testid="approvals-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Approval Workflows</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 22   v4.38–v4.41</p>
      {error && <div data-testid="approvals-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      <div className="flex gap-3 mb-4">
        <button data-testid="approvals-refresh-btn" onClick={loadList} disabled={loading} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">Refresh</button>
        <button data-testid="approvals-create-btn" onClick={handleCreate} disabled={loading} className="px-3 py-1 bg-green-600 text-white rounded text-sm disabled:opacity-50">+ Create</button>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h2 className="text-lg font-semibold mb-2">List</h2>
          {approvals.length > 0 && (
            <div data-testid="approvals-list-ready" className="space-y-2">
              {approvals.map((a: any) => (
                <div key={a.approval_id} data-testid={`approval-row-${a.approval_id}`} onClick={() => loadDetail(a.approval_id)}
                  className={`p-3 rounded border cursor-pointer text-sm ${selectedId === a.approval_id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'}`}>
                  <div className="font-medium">{a.title}</div>
                  <div className="text-xs mt-1"><span className={sc(a.state)}>{a.state}</span>   <span className="text-gray-400">{a.approval_id.slice(0,8)}...</span></div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-2">Detail</h2>
          {detail && (
            <div data-testid="approval-detail-ready" className="bg-gray-50 rounded p-4 text-sm space-y-2">
              <div>Title: {detail.title}</div>
              <div>State: <span className={sc(detail.state)}>{detail.state}</span></div>
              <div className="font-mono text-xs text-gray-400">hash: {detail.approval_hash?.slice(0,16)}...</div>
              <div className="flex gap-2 pt-2">
                {detail.state === 'DRAFT' && (
                  <button data-testid="approval-submit-btn" onClick={() => handleSubmit(detail.approval_id)} disabled={loading} className="px-2 py-1 bg-blue-600 text-white rounded text-xs disabled:opacity-50">Submit</button>
                )}
                {detail.state === 'SUBMITTED' && (
                  <>
                    <button data-testid="approval-approve-btn" onClick={() => handleDecide(detail.approval_id, 'approved')} disabled={loading} className="px-2 py-1 bg-green-600 text-white rounded text-xs disabled:opacity-50">Approve</button>
                    <button data-testid="approval-reject-btn" onClick={() => handleDecide(detail.approval_id, 'rejected')} disabled={loading} className="px-2 py-1 bg-red-600 text-white rounded text-xs disabled:opacity-50">Reject</button>
                  </>
                )}
                {(detail.state === 'APPROVED' || detail.state === 'REJECTED') && (
                  <button data-testid="approval-export-btn" onClick={doExport} disabled={loading} className="px-2 py-1 bg-gray-700 text-white rounded text-xs disabled:opacity-50">Export Pack</button>
                )}
              </div>
            </div>
          )}
          {exportResult && <div data-testid="approval-export-ready" className="mt-2 bg-gray-50 rounded p-3 text-xs font-mono">pack_hash: {exportResult.pack_hash?.slice(0,16)}...</div>}
        </div>
      </div>
    </div>
  );
}
