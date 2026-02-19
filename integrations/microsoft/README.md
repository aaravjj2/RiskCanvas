# Microsoft Agent Framework Integration

This document describes how to integrate RiskCanvas with Microsoft Agent Framework via Model Context Protocol (MCP).

## Overview

RiskCanvas v2.2+ exposes its risk analytics capabilities via MCP endpoints, enabling seamless integration with Microsoft Agent Framework and Azure AI Foundry.

## Architecture

```
Microsoft Agent Framework
  ↓
MCP Protocol (HTTP/JSON)
  ↓
RiskCanvas MCP Server (/mcp/*)
  ↓
Risk Analytics Engine
```

## MCP Endpoints

### 1. List Tools
```
GET /mcp/tools
```

Returns array of available tools with JSON schemas.

Response:
```json
[
  {
    "name": "portfolio_analyze",
    "description": "Analyze portfolio risk metrics",
    "input_schema": { ... }
  },
  ...
]
```

### 2. Call Tool
```
POST /mcp/tools/call
```

Execute a tool with provided arguments.

Request:
```json
{
  "tool_name": "portfolio_analyze",
  "arguments": {
    "portfolio": [...],
    "var_method": "parametric"
  }
}
```

Response:
```json
{
  "tool_name": "portfolio_analyze",
  "result": { "pnl": ..., "var": ... },
  "success": true,
  "error": null
}
```

### 3. Health Check
```
GET /mcp/health
```

Returns MCP server status.

## Available Tools

### portfolio_analyze
Calculates risk metrics for a portfolio:
- Profit & Loss (PnL)
- Value at Risk (VaR)
- Greeks (Delta, Gamma, Vega, Theta)

### report_build
Generates HTML reports with analysis results.

### hedge_suggest
Recommends hedge positions to reduce portfolio risk.

### governance_eval_run
Executes governance evaluation harness for agent configs.

## Azure AI Foundry Integration

### Provider Configuration

Set environment variables:
```bash
FOUNDRY_MODE=foundry  # or 'mock' for testing
AZURE_FOUNDRY_ENDPOINT=https://your-foundry.azure.com
AZURE_FOUNDRY_API_KEY=your_api_key
AZURE_FOUNDRY_DEPLOYMENT=gpt-4
```

### Numbers Policy

The Foundry provider enforces a strict "numbers policy":
- Model output CANNOT invent numeric facts
- Must only reference numbers from provided context data
- Violations raise `NumbersPolicyViolation` exception

This ensures AI-generated narratives remain grounded in actual computed results.

## Agent Framework Wiring Example

### 1. Configure Agent

```python
from azure.ai.agentframework import Agent, Tool

# Create RiskCanvas tools from MCP
portfolio_tool = Tool(
    name="portfolio_analyze",
    description="Analyze portfolio risk",
    endpoint="http://riskcanvas-api:8090/mcp/tools/call",
    input_schema={...}  # From GET /mcp/tools
)

# Create agent with tools
agent = Agent(
    name="RiskAnalyst",
    model="gpt-4",
    tools=[portfolio_tool],
    system_message="You are a risk analysis expert..."
)
```

### 2. Execute Agent Task

```python
# User query
query = "Analyze this portfolio and suggest hedges"

# Agent executes with tools
result = agent.run(query, context={
    "portfolio": [...]
})

# Result includes tool calls and AI narrative
print(result.narrative)  # AI-generated summary
print(result.tool_results)  # Actual computed metrics
```

## Testing Without Real Azure

For local development and CI:

```bash
# Use mock provider (no Azure credentials needed)
FOUNDRY_MODE=mock
DEMO_MODE=true

# Start API
cd apps/api
uvicorn main:app --port 8090

# Test MCP endpoints
curl http://localhost:8090/mcp/tools
curl -X POST http://localhost:8090/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "portfolio_analyze", "arguments": {...}}'
```

## Numbers Policy Validation

Example of policy enforcement:

```python
from foundry_provider import get_foundry_provider

provider = get_foundry_provider()

# Context data (computed facts)
context = {
    "total_pnl": 1525.50,
    "asset_count": 12,
    "var_value": 3421.18
}

# Generate narrative
narrative = provider.generate_text(
    prompt="Summarize portfolio performance",
    context_data=context
)

# Valid: "Portfolio shows $1,525.50 PnL across 12 assets with VaR of $3,421.18"
# Invalid: "Portfolio gained $2,000 with VaR around $4,000" ❌ (invented numbers)
```

The validator extracts numbers from both output and context, ensuring no hallucination.

## Production Checklist

- [ ] Set `FOUNDRY_MODE=foundry` in production
- [ ] Configure Azure Foundry credentials
- [ ] Set `AUTH_MODE=entra` for Entra ID authentication
- [ ] Enable HTTPS for MCP endpoints
- [ ] Monitor numbers policy violations
- [ ] Set up Application Insights for MCP call telemetry
- [ ] Configure rate limiting for MCP endpoints

## Troubleshooting

### MCP endpoints return 401
- Check `AUTH_MODE` and authentication headers
- For testing, use `DEMO_MODE=true` with `x-demo-user`/`x-demo-role` headers

### Foundry provider fails to connect
- Verify `AZURE_FOUNDRY_ENDPOINT` and `AZURE_FOUNDRY_API_KEY`
- Check network connectivity to Azure
- Use `FOUNDRY_MODE=mock` for offline testing

### Numbers policy violations
- Review context_data structure
- Ensure all referenced numbers are in context
- Add exceptions for common values (years, percentages)

## References

- [Microsoft Agent Framework Docs](https://learn.microsoft.com/azure/ai-foundry/agent-framework)
- [Model Context Protocol Spec](https://modelcontextprotocol.io)
- [Azure AI Foundry](https://learn.microsoft.com/azure/ai-foundry/)
- [RiskCanvas MCP Implementation](../../apps/api/mcp_server.py)
- [Foundry Provider Implementation](../../apps/api/foundry_provider.py)
