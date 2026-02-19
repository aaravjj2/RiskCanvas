import { useState, useCallback, useEffect } from 'react';
import { listPipelines, analyzePipeline, generateCiTemplate, exportCiTemplatePack } from '@/lib/api';

const ALL_FEATURES = ['pytest', 'tsc', 'vite_build', 'playwright', 'lint', 'security', 'docker', 'compliance'];

export default function CIPage() {
  const [pipelines, setPipelines] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [selectedPipelineId, setSelectedPipelineId] = useState<string | null>(null);
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>(['pytest', 'tsc', 'vite_build']);
  const [templateResult, setTemplateResult] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPipelines = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await listPipelines(); if (data) setPipelines(data.pipelines ?? []); }
    catch { setError('Failed to load pipelines'); }
    setLoading(false);
  }, []);

  useEffect(() => { loadPipelines(); }, [loadPipelines]);

  const loadAnalysis = useCallback(async (id: string) => {
    setLoading(true); setSelectedPipelineId(id); setAnalysis(null);
    try { const data = await analyzePipeline(id); if (data) setAnalysis(data); }
    catch { setError('Analysis failed'); }
    setLoading(false);
  }, []);

  const doGenerate = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await generateCiTemplate(selectedFeatures); if (data) setTemplateResult(data); }
    catch { setError('Template generation failed'); }
    setLoading(false);
  }, [selectedFeatures]);

  const doExport = useCallback(async () => {
    if (!templateResult) return;
    setLoading(true);
    const data = await exportCiTemplatePack(selectedFeatures);
    if (data) setExportResult(data);
    setLoading(false);
  }, [templateResult, selectedFeatures]);

  const toggleFeature = (f: string) => setSelectedFeatures(prev => prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]);
  const sc = (s: string) => s === 'success' ? 'text-green-600' : s === 'failed' ? 'text-red-600' : 'text-gray-500';

  return (
    <div data-testid="ci-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">CI Intelligence v2</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 24   v4.46–v4.47</p>
      {error && <div data-testid="ci-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Pipelines</h2>
            <button data-testid="ci-refresh-btn" onClick={loadPipelines} disabled={loading} className="px-2 py-1 bg-blue-600 text-white rounded text-xs disabled:opacity-50">Refresh</button>
          </div>
          {pipelines.length > 0 && (
            <div data-testid="ci-list-ready" className="space-y-2">
              {pipelines.map((p: any) => (
                <div key={p.id} data-testid={`ci-pipeline-row-${p.id}`} onClick={() => loadAnalysis(p.id)}
                  className={`p-3 rounded border cursor-pointer text-sm ${selectedPipelineId === p.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'}`}>
                  <div className="font-medium">{p.id}</div>
                  <div className="text-xs mt-1"><span className={sc(p.status)}>{p.status}</span>   {p.ref}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-2">Analysis</h2>
          {analysis && (
            <div data-testid="ci-analysis-ready" className="bg-gray-50 rounded p-4 text-sm space-y-2">
              <div>Category: <span className="text-blue-700 font-medium">{analysis.failure_category}</span></div>
              <div>Health: <span className={sc(analysis.health)}>{analysis.health}</span></div>
              <div className="text-xs font-mono text-gray-400">hash: {analysis.output_hash?.slice(0,16)}...</div>
            </div>
          )}
        </div>
      </div>
      <section className="border-t pt-4">
        <h2 className="text-lg font-semibold mb-3">CI Template Generator</h2>
        <div className="flex flex-wrap gap-2 mb-3">
          {ALL_FEATURES.map(f => (
            <button key={f} data-testid={`ci-feature-${f}`} onClick={() => toggleFeature(f)}
              className={`px-2 py-1 rounded text-xs border ${selectedFeatures.includes(f) ? 'bg-blue-600 text-white border-blue-600' : 'bg-white border-gray-300'}`}>
              {f}
            </button>
          ))}
        </div>
        <div className="flex gap-2 mb-3">
          <button data-testid="ci-generate-btn" onClick={doGenerate} disabled={loading || selectedFeatures.length === 0} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">Generate Template</button>
          <button data-testid="ci-export-btn" onClick={doExport} disabled={loading || !templateResult} className="px-3 py-1 bg-gray-700 text-white rounded text-sm disabled:opacity-50">Export Pack</button>
        </div>
        {templateResult && (
          <div data-testid="ci-template-ready" className="bg-gray-50 rounded p-4">
            <pre className="text-xs font-mono overflow-x-auto max-h-60 overflow-y-auto whitespace-pre-wrap">{templateResult.yaml}</pre>
            <div className="font-mono text-xs text-gray-400 mt-2">hash: {templateResult.output_hash?.slice(0,16)}...</div>
            {exportResult && <div data-testid="ci-export-ready" className="mt-2 text-xs font-mono">pack_hash: {exportResult.pack_hash?.slice(0,16)}...</div>}
          </div>
        )}
      </section>
    </div>
  );
}
