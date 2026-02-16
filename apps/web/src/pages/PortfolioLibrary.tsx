import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  listPortfolios,
  createPortfolio,
  deletePortfolio,
  executeRun,
  DEMO_PORTFOLIO,
} from '@/lib/api';

export default function PortfolioLibrary() {
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<any | null>(null);
  const [portfolioName, setPortfolioName] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    setLoading(true);
    const result = await listPortfolios();
    if (result) {
      setPortfolios(result);
    }
    setLoading(false);
  };

  const handleCreatePortfolio = async () => {
    if (!portfolioName.trim()) return;
    
    const portfolio = {
      id: `portfolio-${Date.now()}`,
      name: portfolioName,
      assets: selectedPortfolio?.portfolio?.assets || DEMO_PORTFOLIO,
    };

    const result = await createPortfolio(portfolio, portfolioName, ['demo']);
    if (result) {
      await loadPortfolios();
      setPortfolioName('');
      alert(`Portfolio saved with ID: ${result.portfolio_id}`);
    }
  };

  const handleDeletePortfolio = async (portfolioId: string) => {
    if (!confirm('Delete this portfolio?')) return;
    
    const result = await deletePortfolio(portfolioId);
    if (result) {
      await loadPortfolios();
      if (selectedPortfolio?.portfolio_id === portfolioId) {
        setSelectedPortfolio(null);
      }
    }
  };

  const handleRunAnalysis = async (portfolio: any) => {
    setLoading(true);
    const result = await executeRun(
      portfolio.portfolio_id,  // Use portfolio_id if available
      portfolio.portfolio,     // Otherwise use portfolio data
      {}
    );
    if (result) {
      alert(`Analysis complete! Run ID: ${result.run_id}`);
    } else {
      alert('Analysis failed. Please check console.');
    }
    setLoading(false);
  };

  const handleLoadSample = () => {
    setSelectedPortfolio({
      portfolio: {
        id: 'sample',
        assets: DEMO_PORTFOLIO,
      },
    });
  };

  const filteredPortfolios = portfolios.filter((p) =>
    p.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div data-testid="portfolio-library-page" className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Portfolio Library</h1>
        <p className="text-gray-600">Manage saved portfolios and run analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Portfolio List */}
        <Card className="p-4">
          <div className="mb-4">
            <h2 className="text-lg font-semibold mb-2">Saved Portfolios</h2>
            <Input
              data-testid="portfolio-search-input"
              placeholder="Search portfolios..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="space-y-2" data-testid="portfolio-list">
            {loading && <p>Loading...</p>}
            {!loading && filteredPortfolios.length === 0 && (
              <p className="text-gray-500">No portfolios found</p>
            )}
            {filteredPortfolios.map((p) => (
              <div
                key={p.portfolio_id}
                data-testid={`portfolio-item-${p.portfolio_id}`}
                className={`p-3 border rounded hover:bg-gray-50 cursor-pointer ${
                  selectedPortfolio?.portfolio_id === p.portfolio_id ? 'bg-blue-50 border-blue-500' : ''
                }`}
                onClick={() => setSelectedPortfolio(p)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{p.name}</p>
                    <p className="text-sm text-gray-500">{p.portfolio_id.substring(0, 12)}...</p>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleRunAnalysis(p)} data-testid={`run-btn-${p.portfolio_id}`}>
                      Run
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeletePortfolio(p.portfolio_id);
                      }}
                      data-testid={`delete-btn-${p.portfolio_id}`}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4">
            <Button onClick={handleLoadSample} data-testid="load-sample-btn" className="w-full">
              Load Sample Portfolio
            </Button>
          </div>
        </Card>

        {/* Right: Portfolio Editor */}
        <Card className="p-4">
          <h2 className="text-lg font-semibold mb-4">Portfolio Editor</h2>

          {selectedPortfolio ? (
            <div data-testid="portfolio-editor">
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Portfolio Name</label>
                <Input
                  data-testid="portfolio-name-input"
                  placeholder="My Portfolio"
                  value={portfolioName}
                  onChange={(e) => setPortfolioName(e.target.value)}
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Assets</label>
                <div className="border rounded p-3 max-h-96 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Symbol</th>
                        <th className="text-right p-2">Quantity</th>
                        <th className="text-right p-2">Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selectedPortfolio.portfolio?.assets || []).map((asset: any, idx: number) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2">{asset.symbol}</td>
                          <td className="text-right p-2">{asset.quantity}</td>
                          <td className="text-right p-2">${asset.price?.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="space-y-2">
                <Button
                  onClick={handleCreatePortfolio}
                  disabled={!portfolioName.trim()}
                  data-testid="save-portfolio-btn"
                  className="w-full"
                >
                  Save Portfolio
                </Button>
                <Button
                  onClick={() => handleRunAnalysis(selectedPortfolio)}
                  variant="secondary"
                  data-testid="run-analysis-btn"
                  className="w-full"
                >
                  Run Analysis
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500" data-testid="no-portfolio-selected">
              <p>Select a portfolio or load a sample to get started</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
