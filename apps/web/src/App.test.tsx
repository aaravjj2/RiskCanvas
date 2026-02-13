import { render, screen, fireEvent } from "@testing-library/react";
import App from "./App";
import { vi, describe, it, expect, beforeEach } from "vitest";

// Mock fetch globally
global.fetch = vi.fn();

describe("App", () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  test("renders app title", () => {
    render(<App />);
    expect(screen.getByTestId("title")).toHaveTextContent("RiskCanvas");
  });

  test("renders app description", () => {
    render(<App />);
    expect(screen.getByText("Deterministic risk preview.")).toBeInTheDocument();
  });

  test("renders Run Risk button", () => {
    render(<App />);
    expect(screen.getByTestId("run-risk-button")).toBeInTheDocument();
  });

  test("calls API when Run Risk button is clicked", async () => {
    const mockResponse = {
      portfolio_id: 1,
      portfolio_name: "Test Portfolio",
      metrics: {
        total_profit_loss: 1500.0,
        total_delta_exposure: 500.0,
        net_delta_exposure: 400.0,
        gross_exposure: 600.0,
        total_value: 3002.5,
        asset_count: 2
      },
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
      ]
    };

    // Mock the fetch response
    (global.fetch as vi.Mock).mockResolvedValueOnce({
      json: () => Promise.resolve(mockResponse),
      ok: true
    });

    render(<App />);

    const button = screen.getByTestId("run-risk-button");
    fireEvent.click(button);

    // Verify fetch was called with correct parameters
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/portfolio/report',
      {
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
      }
    );
  });
});