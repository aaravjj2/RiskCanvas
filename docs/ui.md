# UI Documentation

## Overview

RiskCanvas UI is a single-page React application built with:
- **React 19.2.0** for component rendering
- **React Router v7** for navigation
- **Tailwind CSS v3** for utility-first styling
- **shadcn/ui** for accessible component primitives
- **Vite 7** for build tooling and HMR

## Information Architecture

The application has 6 primary pages accessed through a persistent left sidebar:

1. **Dashboard** (`/`) - Risk metrics overview, KPI cards, analysis triggers
2. **Portfolio** (`/portfolio`) - Position table, add/edit, import/export
3. **Scenarios** (`/scenarios`) - Pre-configured stress tests (market crash, volatility spike, rate hikes)
4. **Agent** (`/agent`) - AI assistant with chat interface and audit log
5. **Reports** (`/reports`) - Historical analysis report generation and viewing
6. **Settings** (`/settings`) - Demo mode toggle, version info, system configuration

## Layout Components

### AppLayout (`src/components/layout/AppLayout.tsx`)

The root layout component wraps all pages with:
- **Sidebar** (64 rem width): Brand header + navigation links
- **Main Content Area**: Responsive container with 1.5rem padding

Key characteristics:
- Sidebar uses React Router `<Link>` for client-side navigation
- Active route highlighted with `bg-accent` background
- Layout enforces consistent spacing across all pages

### Navigation Items

Each nav item has `data-testid="nav-{label}"`:
- `nav-dashboard`
- `nav-portfolio`
- `nav-scenarios`
- `nav-agent`
- `nav-reports`
- `nav-settings`

## Component Patterns

### KPI Cards (Dashboard)

Four cards displayed in a grid:

1. **Portfolio Value** (`kpi-portfolio-value`)
   - Displays total portfolio market value
   - Data source: `portfolioValue` from analysis response

2. **Value at Risk** (`kpi-var`)
   - Shows 95% VaR metric
   - Data source: `var.value` from analysis response

3. **P&L** (`kpi-pnl`)
   - Profit/Loss calculation
   - Data source: `pl` from analysis response

4. **Determinism** (`kpi-determinism`)
   - Displays hash consistency status
   - Data source: `determinism_check` API endpoint

### Charts (Dashboard)

Two placeholder chart cards:

1. **VaR Distribution** (`chart-var-distribution`)
   - Histogram placeholder for risk distribution
   - Future: Monte Carlo simulation results

2. **Top Risk Contributors** (`chart-top-contributors`)
   - Bar chart placeholder for position-level risk attribution
   - Future: Delta/Gamma/Vega exposure breakdown

### Portfolio Table

Displays positions with columns:
- **Symbol** (`table-header-symbol`)
- **Name** (`table-header-name`)
- **Type** (`table-header-type`) - Stock, Call, Put, Bond
- **Quantity** - Position size
- **Price** - Current market price
- **Market Value** - Quantity × Price

Empty state: "No positions in portfolio. Load a sample or add manually."

### Scenario Cards

Three pre-configured stress test scenarios:

1. **Market Crash** (`run-scenario-crash`)
   - -20% equity price shock

2. **Volatility Spike** (`run-scenario-vol`)
   - +50% implied volatility shock

3. **Rate Hikes** (`run-scenario-rate`)
   - +200 bps interest rate shock

## Complete data-testid Catalog

### Layout
- `app-layout` - Root container div
- `sidebar` - Left navigation aside element
- `app-title` - "RiskCanvas" header
- `nav` - Navigation container
- `nav-dashboard`, `nav-portfolio`, `nav-scenarios`, `nav-agent`, `nav-reports`, `nav-settings` - Nav links
- `main-content` - Main content area wrapper

### Dashboard Page
- `dashboard-page` - Page container
- `load-fixture-button` - Load sample portfolio
- `run-risk-button` - Trigger risk analysis
- `determinism-button` - Check calculation determinism
- `kpi-portfolio-value` - Portfolio value KPI card
- `kpi-var` - Value at Risk KPI card
- `kpi-pnl` - P&L KPI card
- `kpi-determinism` - Determinism status KPI card
- `metric-value` - Portfolio value display
- `metric-var` - VaR value display
- `metric-pnl` - P&L value display
- `determinism-status` - Status icon + text
- `determinism-hash` - Hash value display
- `warnings-card` - Warnings container (shown when `warnings` array present)
- `warnings-list` - List of warning messages
- `chart-var-distribution` - VaR distribution chart card
- `chart-top-contributors` - Top risk contributors chart card
- `determinism-section` - Determinism check results section
- `determinism-table` - Determinism check table
- `det-row-{i}` - Individual determinism check row (dynamic index)

### Portfolio Page
- `portfolio-page` - Page container
- `load-sample-button` - Load fixture portfolio
- `export-portfolio-button` - Export to JSON
- `add-position-button` - Add new position
- `portfolio-empty` - Empty state message
- `portfolio-section` - Portfolio table container
- `portfolio-table` - Table element
- `table-header-symbol` - Symbol column header
- `table-header-name` - Name column header
- `table-header-type` - Type column header

### Scenarios Page
- `scenarios-page` - Page container
- `run-scenario-crash` - Market crash scenario button
- `run-scenario-vol` - Volatility spike scenario button
- `run-scenario-rate` - Rate hikes scenario button
- `scenario-results` - Results display card

### Agent Page
- `agent-page` - Page container
- `chat-messages` - Chat messages container
- `chat-input` - Message input textarea
- `chat-send` - Send button
- `audit-log` - Audit log card

### Reports Page
- `reports-page` - Page container
- `reports-list` - List of generated reports
- `generate-report-button` - Generate new report

### Settings Page
- `settings-page` - Page container
- `demo-mode-toggle` - Demo mode checkbox
- `settings-version-info` - Version info card

## API Integration

All API calls use `src/lib/api.ts` with base URL `http://localhost:8090`.

Key endpoints:
- `POST /analyze/portfolio` - Risk analysis (called from Dashboard)
- `GET /determinism/check` - Determinism verification (called from Dashboard)
- `GET /health` - Health check
- `GET /version` - Version info

## State Management

Global state managed via `AppProvider` context (`src/lib/context.tsx`):
- `portfolio` - Array of position objects
- `analysisResult` - Most recent analysis response
- `loading` - Boolean loading state
- `error` - Error message string

## Testing Strategy

All E2E tests use **data-testid selectors only** (no CSS classes, no text matching).

Test files:
- `e2e/test.spec.ts` - Core 6 tests (dashboard load, analysis, navigation, export, determinism, full tour)
- `e2e/tour.spec.ts` - 2-minute demo flow with 9 screenshots and video recording

Playwright configuration:
- **Workers**: 1 (serial execution)
- **Retries**: 0 (strict determinism enforcement)
- **Headed**: true (MCP visibility requirement)
- **Screenshots**: on (captured for every test)
- **Video**: on (TOUR.webm artifact)

## Build & Deployment

### Development
```bash
cd apps/web
npm run dev  # Vite dev server on port 5173
```

### Production
```bash
cd apps/web
npm run build  # Output to apps/web/dist/
npm run preview -- --port 4173  # Serve production build
```

### E2E Testing
```bash
# Start servers first:
# Terminal 1: cd apps/api && uvicorn main:app --port 8090
# Terminal 2: cd apps/web && npm run preview -- --port 4173

# Run tests
npx playwright test --config=e2e/playwright.config.ts
```

## Accessibility

- All interactive elements have `data-testid` attributes for automated testing
- Buttons use semantic HTML (`<button>` elements)
- Navigation uses `<nav>` and `<aside>` landmarks
- shadcn/ui components include ARIA attributes by default

## Future Enhancements

1. **Charts**: Integrate D3.js or Recharts for VaR distribution and risk attribution
2. **Real-time Updates**: WebSocket integration for live portfolio updates
3. **Export Formats**: PDF report generation, CSV export
4. **Dark Mode**: Full theme switching (Tailwind + shadcn/ui support)
5. **Responsive**: Mobile-optimized layouts for tablet/phone form factors
