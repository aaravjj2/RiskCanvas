import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getProvenance, verifyAuditV2Chain } from '@/lib/api';

interface ProvenanceDrawerProps {
  kind: 'run' | 'report' | 'job' | 'policy';
  resourceId: string;
  /** Optional label shown on the trigger button */
  label?: string;
}

interface ProvenanceData {
  kind: string;
  resource_id: string;
  input_hash: string;
  output_hash: string;
  audit_chain_head_hash: string;
  tool_call_hashes: string[];
  related_audit_event_ids: number[];
  lineage: Record<string, unknown>;
}

export function ProvenanceDrawer({ kind, resourceId, label = 'Provenance' }: ProvenanceDrawerProps) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<ProvenanceData | null>(null);
  const [verifyStatus, setVerifyStatus] = useState<'ok' | 'error' | null>(null);
  const [loading, setLoading] = useState(false);

  const handleOpen = async () => {
    setOpen(true);
    if (!data) {
      setLoading(true);
      const result = await getProvenance(kind, resourceId);
      setData(result ?? null);
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    const result = await verifyAuditV2Chain();
    setVerifyStatus(result?.ok ? 'ok' : 'error');
  };

  if (!open) {
    return (
      <Button
        variant="outline"
        size="sm"
        data-testid="provenance-open"
        onClick={handleOpen}
      >
        🔐 {label}
      </Button>
    );
  }

  return (
    <Card className="p-4 mt-2 border border-blue-200 bg-blue-50" data-testid="provenance-drawer">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-blue-900">Provenance — {kind}/{resourceId.substring(0, 12)}…</h3>
        <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>✕</Button>
      </div>

      {loading && <p className="text-xs text-gray-500">Loading provenance…</p>}

      {!loading && !data && (
        <p className="text-xs text-red-500">No provenance record found.</p>
      )}

      {!loading && data && (
        <div className="space-y-2 text-xs font-mono">
          <div>
            <span className="text-gray-500">Input hash:</span>
            <span
              data-testid="provenance-input-hash"
              className="ml-2 text-blue-800 break-all"
            >
              {data.input_hash}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Output hash:</span>
            <span
              data-testid="provenance-output-hash"
              className="ml-2 text-blue-800 break-all"
            >
              {data.output_hash}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Audit chain head:</span>
            <span
              data-testid="provenance-audit-head"
              className="ml-2 text-blue-800 break-all"
            >
              {data.audit_chain_head_hash}
            </span>
          </div>
          {data.tool_call_hashes.length > 0 && (
            <div>
              <span className="text-gray-500">Tool hashes:</span>
              <span className="ml-2 text-gray-700">{data.tool_call_hashes.length} entries</span>
            </div>
          )}
          <div className="pt-2 flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              data-testid="provenance-verify"
              onClick={handleVerify}
            >
              🔍 Verify Chain
            </Button>
            {verifyStatus === 'ok' && (
              <span className="text-green-600 font-semibold" data-testid="provenance-verify-ok">
                ✅ Audit verified
              </span>
            )}
            {verifyStatus === 'error' && (
              <span className="text-red-600 font-semibold" data-testid="provenance-verify-error">
                ❌ Tamper detected
              </span>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
