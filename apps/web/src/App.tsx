export default function App() {
  const handleRunRisk = async () => {
    try {
      const response = await fetch('http://localhost:8000/portfolio/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: 1,
          name: "Test Portfolio",
          assets: [
            {
              symbol: "AAPL",
              name: "Apple Inc.",
              type: "stock",
              quantity: 10,
              price: 150.25
            },
            {
              symbol: "MSFT",
              name: "Microsoft Corporation",
              type: "stock",
              quantity: 5,
              price: 300.50
            }
          ],
          total_value: 3002.50
        })
      });

      const result = await response.json();
      console.log('Risk analysis result:', result);

      // In a real app, we would display the result in the UI
      // For now, we'll just log it to console
      console.log(`Risk analysis complete! Total P&L: ${result.metrics.total_profit_loss}`);
    } catch (error) {
      console.error('Error running risk analysis:', error);
      // In a real app, we would show an error message to the user
    }
  };

  const handleExport = async () => {
    try {
      const response = await fetch('http://localhost:8000/export', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();
      console.log('Export result:', result);

      // In a real app, we would display a success message to the user
      console.log(`Export successful! File saved: ${result.filename}`);
    } catch (error) {
      console.error('Error exporting report:', error);
      // In a real app, we would show an error message to the user
    }
  };

  return (
    <main style={{ padding: 24 }}>
      <h1 data-testid="title">RiskCanvas</h1>
      <p>Deterministic risk preview.</p>
      <button onClick={handleRunRisk} data-testid="run-risk-button">
        Run Risk
      </button>
      <button onClick={handleExport} data-testid="export-button" style={{ marginLeft: 10 }}>
        Export Report
      </button>
    </main>
  );
}
