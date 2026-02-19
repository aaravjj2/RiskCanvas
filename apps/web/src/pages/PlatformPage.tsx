import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { CheckCircle, XCircle, RefreshCw, Wifi, WifiOff, Server, Database, Zap } from "lucide-react";

interface ServiceStatus {
  name: string;
  status: "ok" | "degraded" | "down";
  latency_ms: number;
  details?: string;
}

interface PlatformHealth {
  status: string;
  version: string;
  api_version: string;
  demo_mode: boolean;
  port: number;
  services: ServiceStatus[];
  uptime_hint: string;
  timestamp: string;
}

interface ReadinessState {
  ready: boolean;
  checks: Record<string, boolean>;
  message: string;
}

interface InfraCheck {
  name: string;
  passed: boolean;
  detail: string;
}

interface InfraValidation {
  all_passed: boolean;
  checks: InfraCheck[];
  summary: string;
}

const API = "http://localhost:8090";

function StatusDot({ status }: { status: "ok" | "degraded" | "down" | boolean }) {
  const ok = status === "ok" || status === true;
  const degraded = status === "degraded";
  return (
    <span
      className={`inline-block w-2.5 h-2.5 rounded-full ${
        ok ? "bg-green-500" : degraded ? "bg-yellow-500" : "bg-red-500"
      }`}
    />
  );
}

export default function PlatformPage() {
  const [health, setHealth] = useState<PlatformHealth | null>(null);
  const [readiness, setReadiness] = useState<ReadinessState | null>(null);
  const [liveness, setLiveness] = useState<{ alive: boolean; timestamp: string } | null>(null);
  const [infra, setInfra] = useState<InfraValidation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, r, l, iv] = await Promise.all([
        fetch(`${API}/platform/health/details`).then(res => res.json()),
        fetch(`${API}/platform/readiness`).then(res => res.json()),
        fetch(`${API}/platform/liveness`).then(res => res.json()),
        fetch(`${API}/platform/infra/validate`).then(res => res.json()),
      ]);
      setHealth(h);
      setReadiness(r);
      setLiveness(l);
      setInfra(iv);
    } catch (e) {
      setError("Failed to connect to API. Is the backend running on port 8090?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div data-testid="platform-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Platform Health</h1>
          <p className="text-muted-foreground">Infrastructure readiness and service status</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={load}
          disabled={loading}
          data-testid="platform-refresh-btn"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="rounded-md border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Port badge */}
      {health && (
        <div className="flex gap-2 items-center">
          <Badge variant="secondary" data-testid="platform-port-badge">
            Port {health.port}
          </Badge>
          <Badge variant={health.demo_mode ? "outline" : "default"}>
            {health.demo_mode ? "DEMO Mode" : "Live Mode"}
          </Badge>
          <Badge variant="outline">API v{health.api_version}</Badge>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Health card */}
        <Card data-testid="platform-health-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Server className="h-4 w-4" /> Service Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading...</p>
            ) : health ? (
              <div className="space-y-2">
                {health.services.map(svc => (
                  <div
                    key={svc.name}
                    className="flex items-center justify-between py-1"
                    data-testid={`service-${svc.name}-status`}
                  >
                    <div className="flex items-center gap-2 text-sm">
                      <StatusDot status={svc.status} />
                      <span className="font-medium capitalize">{svc.name}</span>
                      {svc.details && (
                        <span className="text-xs text-muted-foreground">{svc.details}</span>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">{svc.latency_ms}ms</span>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Readiness card */}
        <Card data-testid="platform-readiness-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Wifi className="h-4 w-4" /> Readiness
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading...</p>
            ) : readiness ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {readiness.ready ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  <span className="font-medium">{readiness.message}</span>
                </div>
                {Object.entries(readiness.checks).map(([name, ok]) => (
                  <div key={name} className="flex items-center gap-2 text-sm pl-2">
                    <StatusDot status={ok} />
                    <span className="capitalize">{name}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Liveness card */}
        <Card data-testid="platform-liveness-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Zap className="h-4 w-4" /> Liveness
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading...</p>
            ) : liveness ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {liveness.alive ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <WifiOff className="h-5 w-5 text-red-500" />
                  )}
                  <span className="font-medium">{liveness.alive ? "Alive" : "Not alive"}</span>
                </div>
                <p className="text-xs text-muted-foreground">{liveness.timestamp}</p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Infra validation card */}
        <Card data-testid="platform-infra-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Database className="h-4 w-4" /> Infra Validation
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading...</p>
            ) : infra ? (
              <div className="space-y-2">
                <p className="text-sm font-medium">{infra.summary}</p>
                {infra.checks.map(check => (
                  <div key={check.name} className="flex items-center gap-2 text-sm">
                    <StatusDot status={check.passed} />
                    <span className="font-mono text-xs">{check.name}</span>
                    <span className="text-xs text-muted-foreground truncate">{check.detail}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
