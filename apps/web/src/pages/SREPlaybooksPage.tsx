import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { generateSREPlaybook } from '@/lib/api';

const PHASE_COLOR: Record<string, 'destructive' | 'default' | 'secondary'> = {
  triage: 'destructive',
  mitigate: 'default',
  follow_up: 'secondary',
};

export default function SREPlaybooksPage() {
  const [playbook, setPlaybook] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Incident inputs
  const [policyBlocked, setPolicyBlocked] = useState(false);
  const [pipelineFatals, setPipelineFatals] = useState(0);
  const [degradedServices, setDegradedServices] = useState('');

  const handleGenerate = async () => {
    setLoading(true);
    setPlaybook(null);

    const params: any = {};

    if (policyBlocked) {
      params.policyGateResult = { decision: 'block', reasons: [{ code: 'TOOL_NOT_ALLOWED' }] };
    }

    if (pipelineFatals > 0) {
      params.pipelineAnalysis = { fatal_count: pipelineFatals, categories: ['OOM'] };
    }

    const services = degradedServices.split(',').map(s => s.trim()).filter(Boolean);
    if (services.length > 0) {
      params.platformHealth = { degraded_services: services };
    }

    const result = await generateSREPlaybook(Object.keys(params).length ? params : undefined);
    if (result) setPlaybook(result);
    setLoading(false);
  };

  const handleExport = () => {
    if (!playbook?.playbook_md) return;
    const blob = new Blob([playbook.playbook_md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sre-playbook-${playbook.playbook_hash?.slice(0, 8) || 'export'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div data-testid="sre-page" className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">SRE Playbooks</h1>
        <Badge variant="secondary">v4.0</Badge>
      </div>
      <p className="text-gray-600 text-sm">
        Generate deterministic triage → mitigate → follow-up runbooks for incidents.
        All facts are cited by hash — no invented numbers.
      </p>

      <Card className="p-4 space-y-4">
        <h2 className="text-lg font-semibold">Incident Parameters</h2>

        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="policyBlocked"
            data-testid="sre-param-policy-blocked"
            checked={policyBlocked}
            onChange={e => setPolicyBlocked(e.target.checked)}
            className="w-4 h-4"
          />
          <label htmlFor="policyBlocked" className="text-sm">Policy gate blocked (TOOL_NOT_ALLOWED)</label>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium">Pipeline fatal errors</label>
          <input
            type="number"
            min={0}
            max={10}
            data-testid="sre-param-fatals"
            value={pipelineFatals}
            onChange={e => setPipelineFatals(parseInt(e.target.value) || 0)}
            className="border rounded p-1 w-20 text-sm"
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium">Degraded services (comma-separated)</label>
          <input
            type="text"
            data-testid="sre-param-services"
            value={degradedServices}
            onChange={e => setDegradedServices(e.target.value)}
            placeholder="e.g. order-api, auth-svc"
            className="border rounded p-2 w-full text-sm"
          />
        </div>

        <Button
          onClick={handleGenerate}
          disabled={loading}
          data-testid="sre-generate"
        >
          {loading ? 'Generating playbook…' : 'Generate Playbook'}
        </Button>
      </Card>

      {playbook && (
        <Card className="p-4 space-y-4" data-testid="sre-playbook-ready">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Playbook</h2>
            <Button
              size="sm"
              variant="outline"
              onClick={handleExport}
              data-testid="sre-export-md"
            >
              Export MD
            </Button>
          </div>

          <p className="text-xs text-gray-500 font-mono">Hash: {playbook.playbook_hash}</p>

          {/* Steps timeline */}
          {playbook.playbook_json?.steps?.length > 0 && (
            <div className="space-y-3" data-testid="sre-steps-list">
              {playbook.playbook_json.steps.map((step: any, idx: number) => (
                <div
                  key={idx}
                  className="border-l-4 pl-4 py-2"
                  style={{
                    borderColor: step.phase === 'triage' ? '#ef4444'
                      : step.phase === 'mitigate' ? '#f97316' : '#6b7280'
                  }}
                  data-testid={`sre-step-${idx}`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant={PHASE_COLOR[step.phase] || 'secondary'} className="text-xs uppercase">
                      {step.phase}
                    </Badge>
                    <Badge variant="outline" className="text-xs">{step.priority}</Badge>
                    <span className="font-medium text-sm">{step.title}</span>
                  </div>
                  <p className="text-sm text-gray-600">{step.description}</p>
                  {step.commands?.length > 0 && (
                    <pre className="text-xs font-mono bg-gray-50 rounded p-2 mt-1 overflow-x-auto">
                      {step.commands.join('\n')}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Raw markdown */}
          <details>
            <summary className="text-xs text-gray-500 cursor-pointer">View raw markdown</summary>
            <pre className="text-xs bg-gray-50 border rounded p-3 mt-2 overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto">
              {playbook.playbook_md}
            </pre>
          </details>
        </Card>
      )}
    </div>
  );
}
