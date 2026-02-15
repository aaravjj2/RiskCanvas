import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

export default function Reports() {
  return (
    <div data-testid="reports-page">
      <h1 className="text-3xl font-bold mb-6">Reports</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Report History</CardTitle>
          <CardDescription>View and download past reports</CardDescription>
        </CardHeader>
        <CardContent>
          <div data-testid="reports-list" className="space-y-4">
            <div className="text-muted-foreground text-center py-8">
              No reports generated yet
            </div>
          </div>
          
          <div className="mt-6 pt-6 border-t border-border">
            <Button data-testid="generate-report-button">
              <Download className="h-4 w-4 mr-2" />
              Generate New Report
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
