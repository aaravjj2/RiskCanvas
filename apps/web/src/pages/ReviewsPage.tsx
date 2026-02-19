/**
 * ReviewsPage.tsx (v5.49.0 — Wave 51 + Wave 60 SLA) (v5.31.0 — Wave 51)
 * Route: /reviews
 * data-testids: reviews-page, review-row-{i}, reviews-table-ready, review-submit,
 *               review-approve, review-reject, review-drawer-ready, review-decision-hash
 */
import { useState, useCallback, useEffect } from "react";
import PageShell from "@/components/ui/PageShell";
import { DataTable, type ColumnDef } from "@/components/ui/DataTable";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";

const API = (path: string) => `/api${path}`;

type ReviewStatus = "DRAFT" | "IN_REVIEW" | "APPROVED" | "REJECTED";

interface Review {
  review_id: string;
  tenant_id: string;
  subject_type: string;
  subject_id: string;
  status: ReviewStatus;
  requested_by: string;
  reviewers: string[];
  notes: string;
  decision: string | null;
  decided_by: string | null;
  decision_hash: string | null;
  attestation_id: string | null;
  created_at: string;
  submitted_at: string | null;
  decided_at: string | null;
  [key: string]: unknown;
}

const STATUS_COLORS: Record<ReviewStatus, string> = {
  DRAFT: "bg-gray-700 text-gray-300",
  IN_REVIEW: "bg-yellow-900/40 text-yellow-300",
  APPROVED: "bg-green-900/40 text-green-300",
  REJECTED: "bg-red-900/40 text-red-300",
};

const SUBJECT_TYPES = ["scenario", "run", "artifact", "compliance_pack", "dataset"];

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [selected, setSelected] = useState<Review | null>(null);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");

  // Create form
  const [subjectType, setSubjectType] = useState("scenario");
  const [subjectId, setSubjectId] = useState("");
  const [requestedBy, setRequestedBy] = useState("reviewer@riskcanvas.io");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);

  // Decision form
  const [decidedBy, setDecidedBy] = useState("approver@riskcanvas.io");
  const [submitting, setSubmitting] = useState(false);
  const [approving, setApproving] = useState(false);
  const [rejecting, setRejecting] = useState(false);

  const { addToast } = useToast();

  const loadReviews = useCallback(async () => {
    setLoading(true);
    try {
      const qs = statusFilter ? `?status=${statusFilter}` : "";
      const r = await fetch(API(`/reviews${qs}`));
      if (r.ok) { const d = await r.json(); setReviews(d.reviews ?? []); }
    } catch {}
    setLoading(false);
  }, [statusFilter]);

  useEffect(() => { loadReviews(); }, [loadReviews]);

  async function handleCreate() {
    setCreating(true);
    try {
      const r = await fetch(API("/reviews"), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ subject_type: subjectType, subject_id: subjectId, requested_by: requestedBy, notes }),
      });
      const d = await r.json();
      if (r.ok) {
        addToast("Review created", "success");
        setCreateOpen(false);
        setSubjectId("");
        await loadReviews();
        setSelected(d.review);
      } else {
        addToast(d.detail ?? "Create failed", "error");
      }
    } catch { addToast("Network error", "error"); }
    setCreating(false);
  }

  async function handleSubmit() {
    if (!selected) return;
    setSubmitting(true);
    try {
      const r = await fetch(API(`/reviews/${selected.review_id}/submit`), { method: "POST" });
      const d = await r.json();
      if (r.ok) {
        addToast("Review submitted for approval", "success");
        setSelected(d.review);
        await loadReviews();
      } else {
        addToast(d.detail ?? "Submit failed", "error");
      }
    } catch { addToast("Network error", "error"); }
    setSubmitting(false);
  }

  async function handleDecide(decision: "APPROVED" | "REJECTED") {
    if (!selected) return;
    if (decision === "APPROVED") setApproving(true); else setRejecting(true);
    try {
      const r = await fetch(API(`/reviews/${selected.review_id}/decide`), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ decision, decided_by: decidedBy }),
      });
      const d = await r.json();
      if (r.ok) {
        addToast(`Review ${decision}`, decision === "APPROVED" ? "success" : "error");
        setSelected(d.review);
        await loadReviews();
      } else {
        addToast(d.detail ?? "Decision failed", "error");
      }
    } catch { addToast("Network error", "error"); }
    if (decision === "APPROVED") setApproving(false); else setRejecting(false);
  }

  const columns: ColumnDef<Review>[] = [
    { key: "subject_type", header: "Subject Type", width: "w-36" },
    { key: "subject_id", header: "Subject ID", width: "w-48",
      render: (r: Review) => <span className="font-mono text-xs">{r.subject_id.slice(0, 16)}&hellip;</span>,
    },
    { key: "status", header: "Status", width: "w-28",
      render: (r: Review) => (
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${STATUS_COLORS[r.status]}`}>
          {r.status}
        </span>
      ),
    },
    { key: "requested_by", header: "Requested By", sortable: true, width: "w-44" },
    { key: "created_at", header: "Created", sortable: true, width: "w-44" },
    { key: "_sla", header: "SLA", width: "w-20",
      render: (r: Review) => {
        const sla = (r as Record<string, unknown>).sla_breached as boolean | undefined;
        return sla
          ? <span data-testid="review-sla-breached" className="text-xs px-1.5 py-0.5 rounded bg-red-900/40 text-red-300">⚠ Breached</span>
          : <span className="text-xs text-gray-500">On track</span>;
      },
    },
    { key: "_actions", header: "", width: "w-24",
      render: (row: Review, i: number) => (
        <button
          data-testid={`review-row-${i}`}
          onClick={() => { setSelected(row); setCreateOpen(false); }}
          className="text-xs px-2 py-0.5 rounded border border-gray-600 hover:bg-gray-700"
        >
          Details
        </button>
      ),
    },
  ];

  return (
    <PageShell title="Reviews" subtitle="Collaborative review & sign-off with tamper-evident decision hashes">
      <div data-testid="reviews-page" className="space-y-4">
        {/* Toolbar */}
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
          >
            <option value="">All statuses</option>
            <option value="DRAFT">DRAFT</option>
            <option value="IN_REVIEW">IN_REVIEW</option>
            <option value="APPROVED">APPROVED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
          <div className="flex-1" />
          <button
            onClick={() => { setCreateOpen(true); setSelected(null); }}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
          >
            + New Review
          </button>
        </div>

        {!loading && reviews.length === 0 && (
          <div className="text-center py-12 text-gray-500 text-sm">No reviews found. Click <strong>+ New Review</strong> to start one.</div>
        )}
        {reviews.length > 0 && (
          <DataTable<Review>
            data-testid="reviews-table-ready"
            columns={columns}
            data={reviews}
            rowKey="review_id"
            emptyLabel="No reviews"
          />
        )}
      </div>

      {/* Detail drawer */}
      <RightDrawer open={!!selected && !createOpen} onClose={() => setSelected(null)} title="Review Detail">
        {selected && (
          <div data-testid="review-drawer-ready" className="space-y-4 text-sm">
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Review ID</p><p className="font-mono text-xs break-all text-gray-300">{selected.review_id}</p></div>
            <div className="flex items-center gap-2">
              <p className="text-xs uppercase tracking-widest text-gray-500">Status</p>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${STATUS_COLORS[selected.status]}`}>{selected.status}</span>
            </div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Subject</p><p className="text-gray-200">{selected.subject_type}: <span className="font-mono text-xs">{selected.subject_id}</span></p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Requested By</p><p className="text-gray-200">{selected.requested_by}</p></div>
            {selected.notes && <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Notes</p><p className="text-gray-300">{selected.notes}</p></div>}

            {/* SLA indicator (Wave 60) */}
            {!!(selected as Record<string, unknown>).sla_deadline && (
              <div data-testid="review-sla-indicator" className={`rounded border p-2 ${
                (selected as Record<string, unknown>).sla_breached
                  ? "border-red-700/50 bg-red-900/20"
                  : "border-teal-700/50 bg-teal-900/20"
              }`}>
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-1">SLA (Wave 60)</p>
                <p className="text-xs text-gray-300">Deadline: {(selected as Record<string, unknown>).sla_deadline as string}</p>
                {!!(selected as Record<string, unknown>).assigned_to && (
                  <p className="text-xs text-gray-300">Assigned: {(selected as Record<string, unknown>).assigned_to as string}</p>
                )}
                {(selected as Record<string, unknown>).sla_breached
                  ? <p className="text-xs text-red-400 mt-1">⚠ SLA Breached</p>
                  : <p className="text-xs text-teal-400 mt-1">✓ Within SLA</p>}
              </div>
            )}

            {/* Decision hash (APPROVED / REJECTED) */}
            {selected.decision_hash && (
              <div>
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Decision Hash</p>
                <p data-testid="review-decision-hash" className="font-mono text-xs break-all text-emerald-400">{selected.decision_hash}</p>
              </div>
            )}
            {selected.attestation_id && (
              <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Attestation ID</p><p className="font-mono text-xs break-all text-blue-400">{selected.attestation_id}</p></div>
            )}

            {/* Decided-by field */}
            {selected.status === "IN_REVIEW" && (
              <div>
                <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Decided By</label>
                <input
                  value={decidedBy}
                  onChange={e => setDecidedBy(e.target.value)}
                  className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
                />
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2">
              {selected.status === "DRAFT" && (
                <button
                  data-testid="review-submit"
                  disabled={submitting}
                  onClick={handleSubmit}
                  className="w-full rounded bg-yellow-700 py-2 text-sm font-semibold text-white hover:bg-yellow-600 disabled:opacity-40"
                >
                  {submitting ? "Submitting\u2026" : "Submit for Review"}
                </button>
              )}
              {selected.status === "IN_REVIEW" && (
                <div className="flex gap-2">
                  <button
                    data-testid="review-approve"
                    disabled={approving}
                    onClick={() => handleDecide("APPROVED")}
                    className="flex-1 rounded bg-emerald-700 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:opacity-40"
                  >
                    {approving ? "Approving\u2026" : "\u2713 Approve"}
                  </button>
                  <button
                    data-testid="review-reject"
                    disabled={rejecting}
                    onClick={() => handleDecide("REJECTED")}
                    className="flex-1 rounded bg-red-700 py-2 text-sm font-semibold text-white hover:bg-red-600 disabled:opacity-40"
                  >
                    {rejecting ? "Rejecting\u2026" : "\u2717 Reject"}
                  </button>
                </div>
              )}
              {(selected.status === "APPROVED" || selected.status === "REJECTED") && (
                <p className="text-center text-xs text-gray-500">Decision finalized — no further actions</p>
              )}
            </div>
          </div>
        )}
      </RightDrawer>

      {/* Create drawer */}
      <RightDrawer open={createOpen} onClose={() => setCreateOpen(false)} title="New Review">
        <div className="space-y-4 text-sm">
          <div>
            <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Subject Type</label>
            <select
              value={subjectType}
              onChange={e => setSubjectType(e.target.value)}
              className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
            >
              {SUBJECT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Subject ID</label>
            <input
              value={subjectId}
              onChange={e => setSubjectId(e.target.value)}
              placeholder="e.g. scenario ID, artifact ID…"
              className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Requested By</label>
            <input
              value={requestedBy}
              onChange={e => setRequestedBy(e.target.value)}
              className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Notes</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={3}
              className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
            />
          </div>
          <button
            disabled={creating || !subjectId.trim()}
            onClick={handleCreate}
            className="w-full rounded bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40"
          >
            {creating ? "Creating\u2026" : "Create Review"}
          </button>
        </div>
      </RightDrawer>
    </PageShell>
  );
}
