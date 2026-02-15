import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function Scenarios() {
  return (
    <div data-testid="scenarios-page">
      <h1 className="text-3xl font-bold mb-6">Scenarios</h1>
      
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Market Crash</CardTitle>
            <CardDescription>-20% spot shock</CardDescription>
          </CardHeader>
          <CardContent>
            <Button data-testid="run-scenario-crash" variant="outline" className="w-full">
              Run
            </Button>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Vol Spike</CardTitle>
            <CardDescription>+50% volatility</CardDescription>
          </CardHeader>
          <CardContent>
            <Button data-testid="run-scenario-vol" variant="outline" className="w-full">
              Run
            </Button>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Rate Hike</CardTitle>
            <CardDescription>+100bps rates</CardDescription>
          </CardHeader>
          <CardContent>
            <Button data-testid="run-scenario-rate" variant="outline" className="w-full">
              Run
            </Button>
          </CardContent>
        </Card>
      </div>
      
      <Card data-testid="scenario-results">
        <CardHeader>
          <CardTitle>Results</CardTitle>
          <CardDescription>Scenario impact analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground text-center py-8">
            Run a scenario to see results
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
