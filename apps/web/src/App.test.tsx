import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Portfolio from "./pages/Portfolio";
import { AppProvider } from "./lib/context";
import { vi, describe, it, expect, beforeEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Suppress URL.createObjectURL in jsdom
global.URL.createObjectURL = vi.fn(() => "blob:mock");
global.URL.revokeObjectURL = vi.fn();

// Helper to render with router and context
function renderWithProviders(component: React.ReactElement) {
  return render(
    <MemoryRouter>
      <AppProvider>
        {component}
      </AppProvider>
    </MemoryRouter>
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("renders dashboard with KPI cards", () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByTestId("dashboard-page")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-portfolio-value")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-var")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-pnl")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-determinism")).toBeInTheDocument();
  });

  it("renders action buttons", () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByTestId("load-fixture-button")).toBeInTheDocument();
    expect(screen.getByTestId("run-risk-button")).toBeInTheDocument();
    expect(screen.getByTestId("determinism-button")).toBeInTheDocument();
  });

  it("loads fixture data automatically", async () => {
    renderWithProviders(<Dashboard />);
    // Auto-loads on mount - wait for portfolio value to show
    await waitFor(() => {
      expect(screen.getByTestId("metric-value")).toHaveTextContent("$");
    });
  });

  it("runs risk analysis", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        request_id: "test-001",
        metrics: {
          total_pnl: 200.0,
          total_value: 5000.0,
          asset_count: 2,
          portfolio_greeks: null,
        },
        var: { method: "parametric", var_value: 100.0, confidence_level: 0.95 },
        warnings: [],
      }),
    });
    
    renderWithProviders(<Dashboard />);
    fireEvent.click(screen.getByTestId("run-risk-button"));
    await waitFor(() => {
      expect(screen.getByTestId("metric-pnl")).toHaveTextContent("$200.00");
    });
  });

  it("runs determinism check", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        passed: true,
        checks: [
          { name: 'option_pricing', match: true, hash: 'abc123' },
          { name: 'greeks', match: true, hash: 'def456' },
        ],
        overall_hash: 'test-hash',
      }),
    });
    
    renderWithProviders(<Dashboard />);
    fireEvent.click(screen.getByTestId("determinism-button"));
    await waitFor(() => {
      expect(screen.getByTestId("determinism-section")).toBeInTheDocument();
    });
    expect(screen.getByTestId("determinism-table")).toBeInTheDocument();
  });
});

describe("Portfolio", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("renders portfolio page", () => {
    renderWithProviders(<Portfolio />);
    expect(screen.getByTestId("portfolio-page")).toBeInTheDocument();
  });

  it("shows empty state when no positions", () => {
    renderWithProviders(<Portfolio />);
    expect(screen.getByTestId("portfolio-empty")).toBeInTheDocument();
  });

  it("loads sample portfolio", () => {
    renderWithProviders(<Portfolio />);
    fireEvent.click(screen.getByTestId("load-sample-button"));
    expect(screen.getByTestId("portfolio-section")).toBeInTheDocument();
    expect(screen.getByTestId("portfolio-table")).toBeInTheDocument();
  });

  it("displays portfolio positions in table", () => {
    renderWithProviders(<Portfolio />);
    fireEvent.click(screen.getByTestId("load-sample-button"));
    expect(screen.getByTestId("table-cell-symbol-0")).toHaveTextContent("AAPL");
    expect(screen.getByTestId("table-cell-symbol-1")).toHaveTextContent("MSFT");
  });

  it("exports portfolio to JSON", () => {
    renderWithProviders(<Portfolio />);
    fireEvent.click(screen.getByTestId("load-sample-button"));
    fireEvent.click(screen.getByTestId("export-portfolio-button"));
    // Just verify the button works without errors
    expect(screen.getByTestId("portfolio-table")).toBeInTheDocument();
  });
});
