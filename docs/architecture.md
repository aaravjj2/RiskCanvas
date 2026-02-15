# RiskCanvas Architecture

## System Overview

RiskCanvas is an AI-powered risk analytics platform built for the Microsoft AI Dev Days hackathon. The system provides deterministic financial risk calculations, multi-agent orchestration, and Azure deployment capabilities.

## Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend - React + TypeScript"
        WEB[Web App<br/>React 19.2.0]
        UI[UI Components<br/>data-testid selectors]
    end

    subgraph "API Layer - FastAPI"
        API[FastAPI Server<br/>Port 8090]
        AUTH[Auth Middleware<br/>JWT + Azure AD]
        OBS[Observability<br/>Structured Logging]
        
        subgraph "Endpoints"
            EP1[/analyze/portfolio]
            EP2[/analyze/var]
            EP3[/agent/execute]
            EP4[/report/generate]
        end
    end

    subgraph "Agent System"
        ORCH[Orchestrator Agent<br/>Plan + Execute]
        MULTI[Multi-Agent Coordinator]
        
        subgraph "Specialized Agents"
            INTAKE[Intake Agent<br/>Validation]
            RISK[Risk Agent<br/>Computation]
            REPORT[Report Agent<br/>Narrative]
        end
    end

    subgraph "Computation Engine"
        ENGINE[Python Engine<br/>packages/engine]
        
        subgraph "Core Modules"
            PRICING[pricing.py<br/>Black-Scholes]
            GREEKS[greeks.py<br/>Sensitivities]
            PORTFOLIO[portfolio.py<br/>P&L + Aggregation]
            VAR[var.py<br/>Parametric + Historical]
            SCENARIO[scenario.py<br/>Stress Testing]
        end
        
        CONFIG[config.py<br/>NUMERIC_PRECISION=8]
    end

    subgraph "LLM Integration"
        PROV[Provider Interface]
        MOCK[Mock Provider<br/>DEMO Mode]
        FOUNDRY[Foundry Provider<br/>Real LLM]
    end

    subgraph "MCP Server"
        MCP[JSON-RPC Server<br/>stdio protocol]
        
        subgraph "MCP Tools"
            T1[price_option]
            T2[portfolio_analyze]
            T3[risk_var]
            T4[scenario_run]
            T5[generate_report]
        end
    end

    subgraph "Azure Deployment"
        ACR[Azure Container Registry]
        ACA[Azure Container Apps<br/>Auto-scale 1-10]
        LOGS[Log Analytics]
        INSIGHTS[Application Insights]
    end

    subgraph "Testing"
        PYTEST[pytest<br/>API + Unit Tests]
        VITEST[Vitest<br/>React Tests]
        PLAYWRIGHT[Playwright<br/>E2E Tests]
    end

    %% Frontend connections
    WEB --> UI
    UI -->|HTTP POST| API

    %% API routing
    API --> AUTH
    API --> OBS
    API --> EP1
    API --> EP2
    API --> EP3
    API --> EP4

    %% Endpoint to agent
    EP1 --> ENGINE
    EP2 --> ENGINE
    EP3 --> ORCH
    EP4 --> REPORT

    %% Agent orchestration
    ORCH --> MULTI
    MULTI --> INTAKE
    MULTI --> RISK
    MULTI --> REPORT

    %% Agent to engine
    INTAKE --> ENGINE
    RISK --> ENGINE
    REPORT --> ENGINE

    %% Orchestrator to LLM
    ORCH --> PROV
    PROV --> MOCK
    PROV --> FOUNDRY

    %% Engine modules
    ENGINE --> PRICING
    ENGINE --> GREEKS
    ENGINE --> PORTFOLIO
    ENGINE --> VAR
    ENGINE --> SCENARIO
    ENGINE --> CONFIG

    %% MCP connections
    MCP --> T1
    MCP --> T2
    MCP --> T3
    MCP --> T4
    MCP --> T5
    T1 --> ENGINE
    T2 --> ENGINE
    T3 --> ENGINE
    T4 --> ENGINE
    T5 --> ENGINE

    %% Azure deployment
    API -.Docker Image.-> ACR
    ACR -.Deploy.-> ACA
    ACA --> LOGS
    ACA --> INSIGHTS

    %% Testing
    PYTEST -.Test.-> API
    VITEST -.Test.-> WEB
    PLAYWRIGHT -.E2E.-> WEB
    PLAYWRIGHT -.E2E.-> API

    style WEB fill:#3498db,stroke:#2980b9,color:#fff
    style API fill:#27ae60,stroke:#229954,color:#fff
    style ENGINE fill:#e74c3c,stroke:#c0392b,color:#fff
    style ORCH fill:#f39c12,stroke:#e67e22,color:#fff
    style MCP fill:#9b59b6,stroke:#8e44ad,color:#fff
    style ACA fill:#3498db,stroke:#2980b9,color:#fff
```

## Component Details

### Frontend (React + TypeScript)
- **Framework**: React 19.2.0 with TypeScript 5.9.3
- **Build**: Vite 7.3.1
- **Testing**: Vitest 4.0.18
- **Features**:
  - Portfolio upload (fixtures + custom JSON)
  - Risk analysis visualization
  - Agent interaction interface
  - Report export (HTML)
- **Selectors**: All interactive elements use `data-testid` attributes

### API Layer (FastAPI)
- **Framework**: FastAPI 0.115.0 with Pydantic v2
- **Port**: 8090
- **Middleware**:
  - JWT authentication (Azure AD-ready)
  - Request tracking with unique IDs
  - Structured JSON logging
  - CORS support
- **Endpoints**:
  - POST `/analyze/portfolio` - Portfolio P&L and Greeks
  - POST `/analyze/var` - Value at Risk calculation
  - POST `/agent/execute` - Agent orchestration
  - POST `/report/generate` - HTML report generation

### Computation Engine (Python)
- **Location**: `packages/engine/src/`
- **Determinism**: 8 decimal precision, SHA256 hashing
- **Modules**:
  - `pricing.py`: Black-Scholes option pricing
  - `greeks.py`: Delta, Gamma, Vega, Theta, Rho
  - `portfolio.py`: Aggregated P&L and Greeks
  - `var.py`: Parametric and Historical VaR
  - `scenario.py`: Stress testing with shocks
- **Configuration**: `NUMERIC_PRECISION = 8` in `config.py`

### Agent System
- **Orchestrator**: Plans and executes multi-step workflows
- **Multi-Agent Coordinator**: Routes tasks to specialized agents
- **Agents**:
  - **Intake Agent**: Validates and normalizes inputs
  - **Risk Agent**: Executes computations
  - **Report Agent**: Generates narratives from results
- **Audit**: SHA256 hashes for all handoffs and state changes

### LLM Integration
- **Provider Interface**: Abstraction for LLM calls
- **Mock Provider** (default): Returns deterministic responses, no API key required
- **Foundry Provider**: Real LLM integration (stub for Azure AI Foundry)
- **DEMO Mode**: Uses Mock Provider, all tests pass offline

### MCP Server (Model Context Protocol)
- **Protocol**: JSON-RPC 2.0 over stdio
- **Tools**: 5 whitelisted tools mapping to engine functions
- **Usage**: Can be invoked by external LLM systems
- **Location**: `apps/api/mcp/mcp_server.py`

### Azure Deployment
- **Target**: Azure Container Apps
- **IaC**: Bicep templates in `infra/`
- **Features**:
  - Auto-scaling (1-10 replicas)
  - Container Registry integration
  - Environment variables for DEMO_MODE, LLM_PROVIDER, ENABLE_AUTH
  - Log Analytics + Application Insights
- **Deployment**: `az deployment group create` with `main.bicep`

### Testing
- **pytest**: API and engine unit tests, 0 failures required
- **Vitest**: React component tests, 0 failures required
- **Playwright**: E2E tests with retries=0, workers=1, headless=false
- **Test Gate**: All tests must pass with 0 failed, 0 skipped, 0 retries

## Data Flow

### Typical User Flow
1. User uploads portfolio JSON via frontend
2. Frontend sends POST to `/analyze/portfolio`
3. API validates with Pydantic schemas
4. Engine computes P&L, Greeks, VaR
5. Results returned to frontend
6. User clicks "Ask the Agent"
7. Agent orchestrator plans workflow
8. Multi-agent system executes plan
9. Audit log returned to frontend
10. User exports HTML report

### Agent Execution Flow
1. User provides natural language goal
2. Orchestrator generates structured plan
3. Plan submitted to Multi-Agent Coordinator
4. Coordinator routes to specialized agents:
   - Intake Agent validates inputs
   - Risk Agent computes metrics
   - Report Agent generates narrative
5. Results aggregated and returned
6. Audit log includes SHA256 hashes

## Determinism Guarantees

- **Numeric Precision**: All calculations rounded to 8 decimals
- **Hashing**: SHA256 for state tracking and audit trails
- **No Random Seeds**: Zero randomness in DEMO mode
- **Fixed Timestamps**: Deterministic time handling in tests
- **Same Input → Same Output**: Guaranteed with `DEMO_MODE=true`

## Milestones

- ✅ **v0.1**: Deterministic core engine
- ✅ **v0.2**: API with Pydantic schemas
- ✅ **v0.3**: Agent shell (orchestrator)
- ✅ **v0.4**: Azure MCP server
- ✅ **v0.5**: Foundry integration (Mock + Real)
- ✅ **v0.6**: Multi-agent orchestration
- ✅ **v0.7**: Azure deployment (Bicep, auth, observability)
- 🔄 **v0.8**: Submission polish (E2E tests, UX, docs)

## Proof Pack

Final deliverable includes:
- Test reports (pytest, vitest, playwright)
- Screenshots and videos from E2E tests
- Architecture diagram (this file)
- Deployment guide
- MANIFEST.md with artifact inventory

Location: `/artifacts/proof/<timestamp>-phase0/`

## References

- [CLAUDE.md](../CLAUDE.md) - Development rules
- [DEPLOY.md](../infra/DEPLOY.md) - Azure deployment guide
- [determinism.md](determinism.md) - Numeric stability details
- [Playwright Config](../e2e/playwright_new.config.ts) - E2E test configuration
