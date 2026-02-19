import { useState, useCallback, useEffect } from 'react';
import {
  mrListFixtures, mrPlanReview, mrRunReview, mrCommentPreview,
  mrPostComments, mrExportPack,
} from '@/lib/api';

export default function MRReviewPage() {
  const [fixtures, setFixtures] = useState<any[]>([]);
  const [selectedMr, setSelectedMr] = useState('MR-101');
  const [plan, setPlan] = useState<any>(null);
  const [review, setReview] = useState<any>(null);
  const [comments, setComments] = useState<any[]>([]);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFixtures = useCallback(async () => {
    const data = await mrListFixtures();
    if (data) setFixtures(data.fixtures ?? []);
  }, []);

  useEffect(() => { loadFixtures(); }, [loadFixtures]);

  const doPlan = useCallback(async () => {
    setLoading(true); setError(null); setPlan(null); setReview(null); setComments([]); setExportResult(null);
    try {
      const data = await mrPlanReview(selectedMr, {});
      if (data) setPlan(data);
    } catch { setError('Plan failed'); }
    setLoading(false);
  }, [selectedMr]);

  const doRun = useCallback(async () => {
    if (!plan) return;
    setLoading(true); setError(null);
    try {
      const data = await mrRunReview(plan.plan_id);
      if (data) setReview(data);
    } catch { setError('Run failed'); }
    setLoading(false);
  }, [plan]);

  const doPreview = useCallback(async () => {
    if (!review) return;
    setLoading(true);
    const data = await mrCommentPreview(review.review_id);
    if (data) setComments(data.comments ?? []);
    setLoading(false);
  }, [review]);

  const doPost = useCallback(async () => {
    if (!review || comments.length === 0) return;
    setLoading(true);
    await mrPostComments(review.review_id, comments);
    setLoading(false);
  }, [review, comments]);

  const doExport = useCallback(async () => {
    if (!review) return;
    setLoading(true);
    const data = await mrExportPack(review.review_id);
    if (data) setExportResult(data);
    setLoading(false);
  }, [review]);

  const verdictColor = (v: string) =>
    v === 'BLOCK' ? 'text-red-700 bg-red-100' :
    v === 'REVIEW' ? 'text-yellow-700 bg-yellow-100' :
    'text-green-700 bg-green-100';

  return (
    <div data-testid="mr-review-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Agentic MR Review</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 26 · v4.50–v4.53</p>

      {error && <div data-testid="mr-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Select MR</h2>
        <div className="flex gap-2 flex-wrap mb-3">
          {fixtures.map(f => (
            <button key={f.mr_id} data-testid={`mr-fix-${f.mr_id.toLowerCase()}`}
              onClick={() => setSelectedMr(f.mr_id)}
              className={`px-3 py-1 rounded text-sm border ${selectedMr === f.mr_id ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300'}`}>
              {f.mr_id}: {f.title.slice(0, 30)}
            </button>
          ))}
        </div>
        <div className="flex gap-2 flex-wrap">
          <button data-testid="mr-plan-btn" onClick={doPlan} disabled={loading}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">
            1. Plan Review
          </button>
          <button data-testid="mr-run-btn" onClick={doRun} disabled={loading || !plan}
            className="px-3 py-1 bg-purple-600 text-white rounded text-sm disabled:opacity-50">
            2. Run Review
          </button>
          <button data-testid="mr-preview-btn" onClick={doPreview} disabled={loading || !review}
            className="px-3 py-1 bg-orange-600 text-white rounded text-sm disabled:opacity-50">
            3. Preview Comments
          </button>
          <button data-testid="mr-post-btn" onClick={doPost} disabled={loading || comments.length === 0}
            className="px-3 py-1 bg-gray-700 text-white rounded text-sm disabled:opacity-50">
            4. Post Comments
          </button>
          <button data-testid="mr-export-btn" onClick={doExport} disabled={loading || !review}
            className="px-3 py-1 bg-green-700 text-white rounded text-sm disabled:opacity-50">
            5. Export Pack
          </button>
        </div>
      </section>

      {plan && (
        <div data-testid="mr-plan-ready" className="mb-4 bg-blue-50 rounded p-4 text-sm">
          <div className="font-semibold mb-1">Plan: {plan.plan_id}</div>
          <div className="text-gray-600">MR: {plan.mr_title}</div>
          <div className="text-xs text-gray-400 mt-1">Checklist: {plan.checklist?.join(' → ')}</div>
        </div>
      )}

      {review && (
        <div data-testid="mr-review-ready" className="mb-4 bg-gray-50 rounded p-4 text-sm">
          <div className="flex items-center gap-3 mb-3">
            <span className="font-semibold">Verdict:</span>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${verdictColor(review.verdict)}`}>
              {review.verdict}
            </span>
            <span className="text-xs text-gray-500">
              {review.critical_count} critical · {review.high_count} high · {review.finding_count} total
            </span>
          </div>
          <div className="space-y-1">
            {review.recommendations?.slice(0, 4).map((r: any, i: number) => (
              <div key={i} className="text-xs text-gray-700">
                [{r.severity}] {r.message}
              </div>
            ))}
          </div>
          <div className="font-mono text-xs text-gray-400 mt-2">output_hash: {review.output_hash?.slice(0, 16)}…</div>
        </div>
      )}

      {comments.length > 0 && (
        <div data-testid="mr-comments-ready" className="mb-4 bg-yellow-50 rounded p-4 text-sm">
          <div className="font-semibold mb-2">{comments.length} comment(s) ready to post</div>
          {comments.slice(0, 3).map((c: any, i: number) => (
            <div key={i} className="text-xs text-gray-600 mb-1">{c.body?.slice(0, 80)}…</div>
          ))}
        </div>
      )}

      {exportResult && (
        <div data-testid="mr-export-ready" className="mt-4 bg-gray-50 rounded p-3 text-xs font-mono">
          pack_hash: {exportResult.pack_hash?.slice(0, 16)}… · verdict: {exportResult.verdict} · files: {exportResult.file_count}
        </div>
      )}

      {fixtures.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-semibold mb-2">MR Fixtures ({fixtures.length})</h2>
          <table className="w-full text-xs">
            <thead><tr className="border-b"><th className="text-left py-1">ID</th><th className="text-left py-1">Title</th><th className="text-left py-1">Author</th></tr></thead>
            <tbody>
              {fixtures.map((f: any) => (
                <tr key={f.mr_id} data-testid={`mr-row-${f.mr_id.toLowerCase()}`} className="border-b border-gray-100">
                  <td className="py-1 font-mono">{f.mr_id}</td>
                  <td className="py-1">{f.title}</td>
                  <td className="py-1">{f.author}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
