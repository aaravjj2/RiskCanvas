import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

interface MCPTool {
  name: string;
  description: string;
  input_schema: any;
}

interface ProviderInfo {
  mode: 'mock' | 'foundry';
  connected: boolean;
}

export default function MicrosoftModePage() {
  const [mcpTools, setMcpTools] = useState<MCPTool[]>([]);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo>({ mode: 'mock', connected: false });
  const [loading, setLoading] = useState(true);
  const [testResult, setTestResult] = useState<string | null>(null);
  
  useEffect(() => {
    loadMCPTools();
    loadProviderInfo();
  }, []);
  
  const loadMCPTools = async () => {
    try {
      const response = await fetch('http://localhost:8090/mcp/tools');
      if (response.ok) {
        const tools = await response.json();
        setMcpTools(tools);
      }
    } catch (error) {
      console.error('Failed to load MCP tools:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const loadProviderInfo = async () => {
    try {
      const response = await fetch('http://localhost:8090/mcp/health');
      if (response.ok) {
        const health = await response.json();
        setProviderInfo({
          mode: health.mode || 'mock',
          connected: health.status === 'healthy'
        });
      }
    } catch (error) {
      console.error('Failed to load provider info:', error);
      setProviderInfo({ mode: 'mock', connected: false });
    }
  };
  
  const testMCPCall = async () => {
    setTestResult(null);
    try {
      const response = await fetch('http://localhost:8090/mcp/tools/call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-demo-user': 'demo-user',
          'x-demo-role': 'admin'
        },
        body: JSON.stringify({
          tool_name: 'portfolio_analyze',
          arguments: {
            portfolio: [
              { symbol: 'AAPL', quantity: 10, price: 150.0 }
            ],
            var_method: 'parametric'
          }
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setTestResult(result.success ? 'SUCCESS' : `FAILED: ${result.error}`);
      } else {
        setTestResult(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      setTestResult(`ERROR: ${error}`);
    }
  };
  
  return (
    <div data-testid="microsoft-mode-page" className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Microsoft Mode</h1>
        <p className="text-muted-foreground">
          Azure AI Foundry + Agent Framework integration
        </p>
      </div>
      
      {/* Provider Status */}
      <Card>
        <CardHeader>
          <CardTitle>Azure AI Foundry Provider</CardTitle>
          <CardDescription>Text generation provider status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Provider Mode</div>
                <div className="text-sm text-muted-foreground">
                  {providerInfo.mode === 'mock' 
                    ? 'Mock provider (deterministic, for testing)'
                    : 'Azure AI Foundry (real API calls)'
                  }
                </div>
              </div>
              <Badge 
                data-testid="provider-mode-badge"
                variant={providerInfo.mode === 'foundry' ? 'default' : 'secondary'}
              >
                {providerInfo.mode.toUpperCase()}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Connection Status</div>
                <div className="text-sm text-muted-foreground">
                  MCP server health check
                </div>
              </div>
              <div className="flex items-center gap-2">
                {providerInfo.connected ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="text-sm text-green-500">Connected</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-5 w-5 text-red-500" />
                    <span className="text-sm text-red-500">Disconnected</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* MCP Tools */}
      <Card>
        <CardHeader>
          <CardTitle>MCP Tools</CardTitle>
          <CardDescription
>Available tools exposed via Model Context Protocol</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : mcpTools.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No MCP tools available
            </div>
          ) : (
            <div className="space-y-4" data-testid="mcp-tools-list">
              {mcpTools.map((tool) => (
                <div key={tool.name} className="border rounded-lg p-4 space-y-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-mono font-medium">{tool.name}</div>
                      <div className="text-sm text-muted-foreground">{tool.description}</div>
                    </div>
                    <Badge variant="outline">Tool</Badge>
                  </div>
                  <div className="text-xs font-mono bg-muted p-2 rounded">
                    {JSON.stringify(tool.input_schema, null, 2).substring(0, 200)}
                    {JSON.stringify(tool.input_schema).length > 200 && '...'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Test Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Test MCP Call</CardTitle>
          <CardDescription>Execute a test MCP tool call</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button 
            onClick={testMCPCall}
            data-testid="mcp-test-call-button"
          >
            Test portfolio_analyze
          </Button>
          
          {testResult && (
            <div 
              data-testid="mcp-test-result"
              className={`p-4 rounded-lg ${
                testResult.startsWith('SUCCESS') 
                  ? 'bg-green-50 text-green-900 border border-green-200' 
                  : 'bg-red-50 text-red-900 border border-red-200'
              }`}
            >
              <div className="font-mono text-sm">{testResult}</div>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Agent Framework Integration */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Framework Integration</CardTitle>
          <CardDescription>Microsoft Agent Framework configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Integration Status</span>
              <Badge variant="outline">Ready</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">MCP Endpoint</span>
              <span className="font-mono">/mcp/tools</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tool Count</span>
              <span>{mcpTools.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Numbers Policy</span>
              <Badge variant="secondary">Enforced</Badge>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm text-blue-900">
              <strong>Integration Path:</strong> See <code>/integrations/microsoft</code> for Agent Framework wiring examples.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
