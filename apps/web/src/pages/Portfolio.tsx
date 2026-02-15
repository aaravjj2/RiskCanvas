import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Download } from "lucide-react";
import { useApp } from "@/lib/context";

export default function Portfolio() {
  const { portfolio, loadFixture } = useApp();

  const handleExport = () => {
    const blob = new Blob([JSON.stringify({ portfolio }, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'portfolio.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div data-testid="portfolio-page">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Portfolio</h1>
          <p className="text-muted-foreground">Manage your positions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadFixture} data-testid="load-sample-button">
            Load Sample
          </Button>
          <Button variant="outline" onClick={handleExport} data-testid="export-portfolio-button">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button data-testid="add-position-button">
            <Plus className="h-4 w-4 mr-2" />
            Add Position
          </Button>
        </div>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Positions</CardTitle>
          <CardDescription>{portfolio.length} positions</CardDescription>
        </CardHeader>
        <CardContent>
          {portfolio.length === 0 ? (
            <div data-testid="portfolio-empty" className="text-muted-foreground text-center py-8">
              No positions yet. Load a sample portfolio or add positions manually.
            </div>
          ) : (
            <div className="overflow-x-auto" data-testid="portfolio-section">
              <table className="w-full" data-testid="portfolio-table">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2" data-testid="table-header-symbol">Symbol</th>
                    <th className="text-left py-2 px-2" data-testid="table-header-name">Name</th>
                    <th className="text-left py-2 px-2" data-testid="table-header-type">Type</th>
                    <th className="text-right py-2 px-2" data-testid="table-header-quantity">Quantity</th>
                    <th className="text-right py-2 px-2" data-testid="table-header-price">Price</th>
                    <th className="text-right py-2 px-2">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.map((asset, i) => (
                    <tr key={asset.symbol} className="border-b" data-testid={`table-row-${i}`}>
                      <td className="py-2 px-2 font-medium" data-testid={`table-cell-symbol-${i}`}>{asset.symbol}</td>
                      <td className="py-2 px-2" data-testid={`table-cell-name-${i}`}>{asset.name}</td>
                      <td className="py-2 px-2" data-testid={`table-cell-type-${i}`}>{asset.type}</td>
                      <td className="py-2 px-2 text-right" data-testid={`table-cell-quantity-${i}`}>{asset.quantity}</td>
                      <td className="py-2 px-2 text-right" data-testid={`table-cell-price-${i}`}>${asset.price.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right">${(asset.quantity * asset.price).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="font-bold">
                    <td colSpan={5} className="py-2 px-2 text-right">Total:</td>
                    <td className="py-2 px-2 text-right">
                      ${portfolio.reduce((sum, a) => sum + (a.quantity * a.price), 0).toFixed(2)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
