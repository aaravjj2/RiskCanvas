/**
 * DatasetsPage.tsx (v5.47.0 — Wave 49 + Wave 58 provenance)
 * Route: /datasets
 * data-testids: datasets-page, dataset-row-{i}, dataset-ingest-open, dataset-validate-btn,
 *               dataset-save-btn, datasets-table-ready, dataset-drawer-ready, dataset-kind-filter
 */
import { useState, useCallback, useEffect } from "react";
import PageShell from "@/components/ui/PageShell";
import { DataTable, type ColumnDef } from "@/components/ui/DataTable";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";

const API = (path: string) => `/api${path}`;

type DatasetKind = "portfolio" | "rates_curve" | "stress_preset" | "fx_set" | "credit_curve" | "";

interface Dataset {
  dataset_id: string;
  tenant_id: string;
  kind: string;
  name: string;
  row_count: number;
  sha256: string;
  schema_version: string;
  verified: boolean;
  created_at: string;
  created_by: string;
  payload?: unknown;
  [key: string]: unknown;
}

interface ValidationError { path: string; message: string }

const KIND_OPTIONS: Array<{ value: DatasetKind; label: string }> = [
  { value: "", label: "All kinds" },
  { value: "portfolio", label: "Portfolio" },
  { value: "rates_curve", label: "Rates Curve" },
  { value: "stress_preset", label: "Stress Preset" },
  { value: "fx_set", label: "FX Set" },
  { value: "credit_curve", label: "Credit Curve" },
];

const KIND_COLORS: Record<string, string> = {
  portfolio: "bg-blue-900/40 text-blue-300",
  rates_curve: "bg-purple-900/40 text-purple-300",
  stress_preset: "bg-orange-900/40 text-orange-300",
  fx_set: "bg-teal-900/40 text-teal-300",
  credit_curve: "bg-red-900/40 text-red-300",
};

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selected, setSelected] = useState<Dataset | null>(null);
  const [loading, setLoading] = useState(true);
  const [ingestOpen, setIngestOpen] = useState(false);
  const [kindFilter, setKindFilter] = useState<DatasetKind>("");
  const [provenance, setProvenance] = useState<Record<string, unknown> | null>(null);

  // Ingest form state
  const [ingestKind, setIngestKind] = useState<DatasetKind>("portfolio");
  const [ingestName, setIngestName] = useState("");
  const [ingestPayload, setIngestPayload] = useState("{}");
  const [ingestCreatedBy, setIngestCreatedBy] = useState("demo@riskcanvas.io");
  const [ingestErrors, setIngestErrors] = useState<ValidationError[]>([]);
  const [validating, setValidating] = useState(false);
  const [saving, setSaving] = useState(false);

  const { addToast } = useToast();

  const loadDatasets = useCallback(async () => {
    setLoading(true);
    try {
      const qs = kindFilter ? `?kind=${kindFilter}` : "";
      const r = await fetch(API(`/datasets${qs}`));
      if (r.ok) { const d = await r.json(); setDatasets(d.datasets ?? []); }
    } catch {}
    setLoading(false);
  }, [kindFilter]);

  useEffect(() => { loadDatasets(); }, [loadDatasets]);

  useEffect(() => {
    if (!selected) { setProvenance(null); return; }
    fetch(API(`/provenance/datasets/${selected.dataset_id}`))
      .then(r => r.ok ? r.json() : null)
      .then(d => setProvenance(d?.dataset ?? null))
      .catch(() => setProvenance(null));
  }, [selected]);

  async function handleValidate() {
    setValidating(true);
    setIngestErrors([]);
    try {
      let parsed: unknown;
      try { parsed = JSON.parse(ingestPayload); } catch { setIngestErrors([{ path: "$", message: "Invalid JSON" }]); setValidating(false); return; }
      const r = await fetch(API("/datasets/validate"), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ kind: ingestKind, name: ingestName, payload: parsed }),
      });
      const d = await r.json();
      if (d.valid) {
        addToast("Payload is valid \u2713", "success");
        setIngestErrors([]);
      } else {
        setIngestErrors(d.errors ?? []);
        addToast(`${d.errors?.length ?? 0} validation error(s)`, "error");
      }
    } catch { addToast("Validation request failed", "error"); }
    setValidating(false);
  }

  async function handleSave() {
    setSaving(true);
    try {
      let parsed: unknown;
      try { parsed = JSON.parse(ingestPayload); } catch { addToast("Invalid JSON payload", "error"); setSaving(false); return; }
      const r = await fetch(API("/datasets/ingest"), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ kind: ingestKind, name: ingestName, payload: parsed, created_by: ingestCreatedBy }),
      });
      const d = await r.json();
      if (r.ok && d.valid) {
        addToast(`Dataset ingested — ${d.dataset.row_count} rows`, "success");
        setIngestOpen(false);
        setIngestPayload("{}");
        setIngestName("");
        setIngestErrors([]);
        await loadDatasets();
      } else {
        setIngestErrors(d.errors ?? []);
        addToast("Ingestion failed — check errors", "error");
      }
    } catch { addToast("Network error", "error"); }
    setSaving(false);
  }

  const columns: ColumnDef<Dataset>[] = [
    { key: "name", header: "Name", sortable: true },
    { key: "kind", header: "Kind", width: "w-36",
      render: (r: Dataset) => (
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${KIND_COLORS[r.kind] ?? "bg-gray-700 text-gray-300"}`}>
          {r.kind.replace("_", " ")}
        </span>
      ),
    },
    { key: "row_count", header: "Rows", width: "w-16" },
    { key: "schema_version", header: "Schema", width: "w-20" },
    { key: "verified", header: "Verified", width: "w-20",
      render: (r: Dataset) => (
        <span className={`text-xs font-semibold ${r.verified ? "text-green-400" : "text-red-400"}`}>
          {r.verified ? "\u2713 OK" : "\u2717"}
        </span>
      ),
    },
    { key: "created_at", header: "Created", sortable: true, width: "w-44" },
    { key: "_lic", header: "License", width: "w-24",
      render: (_r: Dataset, i: number) => (
        <span data-testid={`dataset-license-badge-${i}`} className="text-xs px-1.5 py-0.5 rounded bg-teal-900/40 text-teal-300">
          {(_r as Record<string, unknown>).license_tag as string ?? "—"}
        </span>
      ),
    },
    { key: "_actions", header: "", width: "w-24",
      render: (row: Dataset, i: number) => (
        <button
          data-testid={`dataset-row-${i}`}
          onClick={() => { setSelected(row); setIngestOpen(false); }}
          className="text-xs px-2 py-0.5 rounded border border-gray-600 hover:bg-gray-700"
        >
          Details
        </button>
      ),
    },
  ];

  return (
    <PageShell title="Datasets" subtitle="Dataset Ingestion v1 — portfolios, rate curves, stress presets, FX sets & credit curves">
      <div data-testid="datasets-page" className="space-y-4">
        {/* Toolbar */}
        <div className="flex items-center gap-3 flex-wrap">
          <select
            data-testid="dataset-kind-filter"
            value={kindFilter}
            onChange={e => setKindFilter(e.target.value as DatasetKind)}
            className="text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
          >
            {KIND_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <div className="flex-1" />
          <button
            data-testid="dataset-ingest-open"
            onClick={() => { setIngestOpen(true); setSelected(null); }}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
          >
            + Ingest Dataset
          </button>
        </div>

        {/* Table */}
        {!loading && datasets.length === 0 && (
          <div className="text-center py-12 text-gray-500 text-sm">No datasets found. Click <strong>+ Ingest Dataset</strong> to add one.</div>
        )}
        {datasets.length > 0 && (
          <DataTable<Dataset>
            data-testid="datasets-table-ready"
            columns={columns}
            data={datasets}
            rowKey="dataset_id"
            emptyLabel="No datasets"
          />
        )}
      </div>

      {/* Detail drawer */}
      <RightDrawer open={!!selected && !ingestOpen} onClose={() => setSelected(null)} title="Dataset Detail">
        {selected && (
          <div data-testid="dataset-drawer-ready" className="space-y-4 text-sm">
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Dataset ID</p><p className="font-mono text-xs break-all text-gray-300">{selected.dataset_id}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Name</p><p className="text-gray-200">{selected.name}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Kind</p><span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${KIND_COLORS[selected.kind] ?? "bg-gray-700 text-gray-300"}`}>{selected.kind}</span></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Row Count</p><p className="text-gray-200">{selected.row_count}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Schema Version</p><p className="text-gray-200">{selected.schema_version}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Verified</p><p className={selected.verified ? "text-green-400" : "text-red-400"}>{selected.verified ? "\u2713 Verified" : "\u2717 Unverified"}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">SHA-256</p><p className="font-mono text-xs break-all text-gray-400">{selected.sha256}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Created By</p><p className="text-gray-200">{selected.created_by}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Created At</p><p className="text-gray-200">{selected.created_at}</p></div>
            {provenance && (
              <div data-testid="dataset-provenance-badge" className="rounded border border-teal-700/50 bg-teal-900/20 p-3 space-y-2">
                <p className="text-xs uppercase tracking-widest text-teal-400 mb-1">Provenance (Wave 58)</p>
                <div className="flex gap-2 flex-wrap">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-teal-900/40 text-teal-300">{(provenance.license_tag as string) ?? "—"}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-300">{(provenance.source_type as string) ?? "—"}</span>
                  {(provenance.license_compliant as boolean) && <span className="text-xs text-green-400">✓ Compliant</span>}
                </div>
                <p className="text-xs text-gray-400">{(provenance.source_note as string) ?? ""}</p>
                <p className="text-xs font-mono break-all text-gray-500">{(provenance.checksum as string) ?? ""}</p>
              </div>
            )}
          </div>
        )}
      </RightDrawer>

      {/* Ingest drawer */}
      <RightDrawer open={ingestOpen} onClose={() => { setIngestOpen(false); setIngestErrors([]); }} title="Ingest Dataset">
        <div className="space-y-4 text-sm">
          <div>
            <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Kind</label>
            <select
              value={ingestKind}
              onChange={e => setIngestKind(e.target.value as DatasetKind)}
              className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
            >
              {KIND_OPTIONS.filter(o => o.value !== "").map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Name</label>
            <input
              value={ingestName}
              onChange={e => setIngestName(e.target.value)}
              placeholder="e.g. Q1 2026 Portfolio"
              className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Created By</label>
            <input
              value={ingestCreatedBy}
              onChange={e => setIngestCreatedBy(e.target.value)}
              className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Payload (JSON)</label>
            <textarea
              value={ingestPayload}
              onChange={e => setIngestPayload(e.target.value)}
              rows={8}
              className="w-full font-mono text-xs rounded border border-gray-600 bg-gray-900 text-gray-200 px-2 py-1.5"
            />
          </div>
          {ingestErrors.length > 0 && (
            <div className="rounded border border-red-800 bg-red-900/20 p-3 space-y-1">
              {ingestErrors.map((e, i) => (
                <p key={i} className="text-xs text-red-400"><span className="font-mono">{e.path}</span>: {e.message}</p>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            <button
              data-testid="dataset-validate-btn"
              disabled={validating}
              onClick={handleValidate}
              className="flex-1 rounded border border-gray-600 py-2 text-sm font-semibold text-gray-200 hover:bg-gray-700 disabled:opacity-40"
            >
              {validating ? "Validating\u2026" : "Validate"}
            </button>
            <button
              data-testid="dataset-save-btn"
              disabled={saving}
              onClick={handleSave}
              className="flex-1 rounded bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40"
            >
              {saving ? "Saving\u2026" : "Save"}
            </button>
          </div>
        </div>
      </RightDrawer>
    </PageShell>
  );
}
