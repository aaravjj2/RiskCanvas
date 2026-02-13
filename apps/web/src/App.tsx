import React, { useState } from 'react';

export default function App() {
  const [tableData, setTableData] = useState([]);

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

  const handleLoadFixture = async () => {
    try {
      // Simulate loading data from fixtures
      const fixtureData = {
        id: 1,
        name: "Tech Growth Portfolio",
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
      };

      // Set the table data to display in the UI
      setTableData(fixtureData.assets);
      console.log('Fixture data loaded:', fixtureData);
    } catch (error) {
      console.error('Error loading fixture:', error);
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
      <button onClick={handleLoadFixture} data-testid="load-fixture-button" style={{ marginLeft: 10 }}>
        Load Fixture
      </button>
      <button onClick={handleExport} data-testid="export-button" style={{ marginLeft: 10 }}>
        Export Report
      </button>

      {/* Display table when fixture is loaded */}
      {tableData.length > 0 && (
        <table style={{ marginTop: 20 }}>
          <thead>
            <tr>
              <th data-testid="table-header-symbol">Symbol</th>
              <th data-testid="table-header-name">Name</th>
              <th data-testid="table-header-type">Type</th>
              <th data-testid="table-header-quantity">Quantity</th>
              <th data-testid="table-header-price">Price</th>
            </tr>
          </thead>
          <tbody>
            {tableData.map((asset, index) => (
              <tr key={index} data-testid={`table-row-${index}`}>
                <td data-testid={`table-cell-symbol-${index}`}>{asset.symbol}</td>
                <td data-testid={`table-cell-name-${index}`}>{asset.name}</td>
                <td data-testid={`table-cell-type-${index}`}>{asset.type}</td>
                <td data-testid={`table-cell-quantity-${index}`}>{asset.quantity}</td>
                <td data-testid={`table-cell-price-${index}`}>{asset.price}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
