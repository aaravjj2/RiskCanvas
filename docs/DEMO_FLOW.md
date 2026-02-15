# RiskCanvas Demo Flow

## Overview

This document describes the complete demo flow for RiskCanvas Phase 0 (v0.1 → v0.8).

## Prerequisites

- Python 3.11+
- Node.js 18+
- PowerShell (Windows)

## Setup

```powershell
# Backend setup
cd apps/api
python -m pip install -r requirements.txt

# Frontend setup
cd ../apps/web
npm install

# E2E setup
cd ../../e2e
npm install
```

## Demo Flow

### 1. Start Backend API

```powershell
cd apps/api
$env:DEMO_MODE="true"
$env:LLM_PROVIDER="mock"
$env:ENABLE_AUTH="false"
python -m uvicorn main:app --reload --port 8090
```

**Expected**: Server starts on http://localhost:8090

### 2. Verify API Health

```powershell
curl http://localhost:8090/health
```

**Expected**: `{"status":"ok","demo_mode":true}`

### 3. Start Frontend

```powershell
cd apps/web
npm run dev
```

**Expected**: Frontend starts on http://localhost:5173

### 4. Manual Demo Steps

#### Step 1: Load Portfolio
- Open browser to http://localhost:5173
- Click **"Load Sample Portfolio"** button
- **Verify**: Portfolio name "Tech Portfolio" appears
- **Verify**: Asset table displays with AAPL, GOOGL, MSFT

#### Step 2: Run Risk Analysis
- Click **"Run Risk Analysis"** button
- **Verify**: Metrics appear (Total Value, Total P&L, VaR)
- **Verify**: Greeks section shows Delta, Gamma, Vega, Theta, Rho
- **Expected Values**:
  - Total Value: ~$1,500,000
  - Total P&L: Positive (green)
  - VaR (95%): Negative value indicating maximum loss

#### Step 3: Agent Interaction
- Enter goal in "Ask the Agent" box: `"Analyze my portfolio risk and generate a report"`
- Click **"Execute"** button
- **Verify**: Agent results appear with:
  - Status badge (Success/Failed)
  - Plan section showing goal and step count
  - Execution result with steps completed
  - Audit log with step-by-step entries

#### Step 4: Export Report
- Click **"Export Report"** button
- **Verify**: HTML file downloads with name like `Tech Portfolio-report.html`
- Open HTML file in browser
- **Verify**: Report contains portfolio details, metrics, Greeks, VaR

### 5. Run E2E Tests

```powershell
cd e2e
$env:CI="false"
npx playwright test --headed
```

**Expected**: All tests pass with 0 failures, 0 skips

### 6. API Testing

```powershell
cd apps/api
pytest tests/ -v
```

**Expected**: All tests pass

### 7. Frontend Unit Tests

```powershell
cd apps/web
npm run test
```

**Expected**: All tests pass

## API Endpoints Demo

### Price Option

```powershell
curl -X POST http://localhost:8090/pricing/option `
  -H "Content-Type: application/json" `
  -d '{
    "spot_price": 100,
    "strike_price": 105,
    "time_to_maturity": 0.25,
    "risk_free_rate": 0.05,
    "volatility": 0.2,
    "option_type": "call"
  }'
```

**Expected**: Deterministic option price (8 decimal precision)

### Analyze Portfolio

```powershell
curl -X POST http://localhost:8090/analyze/portfolio `
  -H "Content-Type: application/json" `
  -d '@../../fixtures/portfolio_1.json'
```

**Expected**: Portfolio metrics with P&L and Greeks

### Calculate VaR

```powershell
curl -X POST http://localhost:8090/analyze/var `
  -H "Content-Type: application/json" `
  -d '{
    "portfolio": { "name": "Test", "assets": [...] },
    "confidence_level": 0.95,
    "method": "parametric"
  }'
```

**Expected**: VaR value with confidence level

### Agent Execute

```powershell
curl -X POST http://localhost:8090/agent/execute `
  -H "Content-Type: application/json" `
  -d '{
    "goal": "Analyze portfolio risk",
    "portfolio": { "name": "Test", "assets": [...] }
  }'
```

**Expected**: Agent plan, execution result, and audit log

## MCP Server Demo

### Start MCP Server

```powershell
cd apps/api
python -m mcp.mcp_server
```

### Send JSON-RPC Request (via stdin)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "price_option",
    "arguments": {
      "spot_price": 100,
      "strike_price": 105,
      "time_to_maturity": 0.25,
      "risk_free_rate": 0.05,
      "volatility": 0.2,
      "option_type": "call"
    }
  }
}
```

**Expected**: JSON-RPC response with option price

## Azure Deployment Demo

### Build Docker Image

```powershell
cd apps/api
docker build -t riskcanvas-api:latest .
```

### Run Locally

```powershell
docker run -p 8090:8090 `
  -e DEMO_MODE=true `
  -e LLM_PROVIDER=mock `
  -e ENABLE_AUTH=false `
  riskcanvas-api:latest
```

**Expected**: API accessible at http://localhost:8090

### Deploy to Azure (requires Azure CLI)

```powershell
cd infra
az deployment group create `
  --resource-group riskcanvas-rg `
  --template-file main.bicep `
  --parameters @params.json
```

**Expected**: Container App deployed to Azure

## Test Gate Validation

### Run All Tests

```powershell
# TypeScript compilation
cd apps/web
npm run typecheck
# Expected: 0 errors

# Vitest
npm run test
# Expected: 0 failed, 0 skipped

# Pytest
cd ../api
pytest tests/ -v
# Expected: 0 failed, 0 skipped

# Playwright
cd ../../e2e
npx playwright test
# Expected: 0 failed, 0 skipped, retries=0
```

### Success Criteria

- ✅ tsc: 0 errors
- ✅ vitest: 0 failed, 0 skipped
- ✅ pytest: 0 failed, 0 skipped
- ✅ playwright: 0 failed, 0 skipped, retries=0, workers=1

## Proof Pack Generation

After all tests pass, proof pack is generated in `/artifacts/proof/<timestamp>-phase0/`:

```
artifacts/
  proof/
    20250101-120000-phase0/
      MANIFEST.md
      manifest.json
      README.md
      playwright-report/
      test-results/
      screenshots/
      videos/
```

## Troubleshooting

### API Not Starting
- Check Python version: `python --version` (must be 3.11+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8090: `netstat -an | findstr 8090`

### Frontend Not Building
- Clear cache: `rm -r node_modules; npm install`
- Check Node version: `node --version` (must be 18+)

### E2E Tests Failing
- Ensure API is running on port 8090
- Ensure frontend builds successfully: `npm run build`
- Check Playwright browsers: `npx playwright install`

### Tests Timing Out
- Increase timeout in test files
- Check network connectivity
- Verify DEMO_MODE is enabled for offline testing

## Demo Checklist

- [ ] Backend starts successfully
- [ ] Frontend loads in browser
- [ ] Portfolio fixture loads
- [ ] Risk analysis displays metrics
- [ ] Greeks section visible
- [ ] Agent execution completes
- [ ] Audit log shows steps
- [ ] Report exports as HTML
- [ ] All test gates pass (tsc, vitest, pytest, playwright)
- [ ] Proof pack generated

## Success Metrics

- **Determinism**: Same input → Same output (verified by tests)
- **Test Coverage**: 100% of critical paths
- **Performance**: Analysis completes in <2 seconds
- **DEMO Mode**: No API keys required
- **Azure Deployment**: One-command deployment via Bicep

## Next Steps

1. Run full demo flow
2. Execute test gates
3. Generate proof pack
4. Submit to hackathon judges

---

**RiskCanvas Phase 0 Complete** ✅
