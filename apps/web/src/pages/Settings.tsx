import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

export default function Settings() {
  return (
    <div data-testid="settings-page">
      <h1 className="text-3xl font-bold mb-6">Settings</h1>
      
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Environment</CardTitle>
            <CardDescription>Configure application mode</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="demo-mode">DEMO Mode</Label>
                <div className="text-sm text-muted-foreground">
                  Use mock data without API keys
                </div>
              </div>
              <Switch
                id="demo-mode"
                data-testid="demo-mode-toggle"
                defaultChecked={true}
              />
            </div>
          </CardContent>
        </Card>
        
        <Card data-testid="settings-version-info">
          <CardHeader>
            <CardTitle>Version Information</CardTitle>
            <CardDescription>Application and engine versions</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">API Version</dt>
                <dd className="font-mono">1.0.0</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Engine Version</dt>
                <dd className="font-mono">0.1.0</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Status</dt>
                <dd className="text-green-500">Healthy</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
