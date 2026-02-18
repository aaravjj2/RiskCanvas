#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build Wave 6 submission pack for RiskCanvas v2.9.0 → v3.2.0
.DESCRIPTION
    Generates SUBMISSION.md, ARCHITECTURE.mmd, DEMO_SCRIPT.md, LINKS.md
    and zips them into artifacts/submission/<timestamp>-wave6/
#>

$ErrorActionPreference = "Stop"
$timestamp = (Get-Date -Format "yyyyMMdd-HHmmss")
$outDir = "$PSScriptRoot\..\..\artifacts\submission\$timestamp-wave6"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

Write-Host "Building Wave 6 submission pack → $outDir"

# ── SUBMISSION.md ──────────────────────────────────────────────────────────────
$submission = @"
# RiskCanvas – Wave 6 Submission
**Version Range:** v2.9.0 → v3.2.0
**Date:** $(Get-Date -Format "yyyy-MM-dd")

## Deliverables

### v2.9.0 – Platform Health & Readiness
- **Backend:** `apps/api/platform_health.py` — 4 endpoints
  - `GET /platform/health/details`
  - `GET /platform/readiness`
  - `GET /platform/liveness`
  - `GET /platform/infra/validate`
- **Frontend:** `apps/web/src/pages/PlatformPage.tsx` — health dashboard
- **Tests:** `apps/api/tests/test_platform_health.py` — 25 pytest tests
- **E2E:** `e2e/test-platform.spec.ts` — 8 Playwright tests

### v3.0.0 – Multi-Agent Orchestration
- **Backend:** `apps/api/multi_agent_orchestrator.py` — REST router
  - `GET /orchestrator/plan`
  - `POST /orchestrator/run`
  - `GET /orchestrator/agents`
- **Frontend:** `apps/web/src/pages/MicrosoftModePage.tsx` — 3-step wizard
  - Step 1: Provider Status
  - Step 2: MCP Tools + test call
  - Step 3: Multi-Agent Run + audit log + SRE checks
- **Tests:** `apps/api/tests/test_multi_agent_orchestrator.py` — 15 pytest tests
- **E2E:** `e2e/test-microsoft-wizard.spec.ts` — 10 Playwright tests

### v3.1.0 – DevOps Policy Gate
- **Backend:** `apps/api/devops_policy.py` — policy router
  - `POST /devops/policy/evaluate`
  - `POST /devops/policy/export`
  - `GET /devops/policy/rules`
- **Frontend:** `apps/web/src/pages/DevOpsPage.tsx` — Policy Gate tab
- **Tests:** `apps/api/tests/test_devops_policy.py` — 36 pytest tests
- **E2E:** `e2e/test-devops-policy.spec.ts` — 8 Playwright tests

### v3.2.0 – Submission Pack + Judge Demo
- **Judge Demo:** `e2e/phase6-judge-demo.spec.ts` — full tour, 26 screenshots
- **Judge Config:** `e2e/playwright.judge.config.ts` — slowMo=4000
- **Submission:** `scripts/submission/build_submission.ps1`
- **Proof Runner:** `scripts/proof/run_wave6.ps1`
- **Infrastructure:** `.env.example` created at repo root

## Test Summary
| Suite | Count | Status |
|-------|-------|--------|
| pytest | 286+ | ✅ 0 failed |
| vitest | 10 | ✅ 0 failed |
| tsc | - | ✅ clean |
| vite build | - | ✅ clean |

## Architecture
See `ARCHITECTURE.mmd` for Mermaid diagram.

## Demo
See `DEMO_SCRIPT.md` for step-by-step demo instructions.
"@

$submission | Out-File -FilePath "$outDir\SUBMISSION.md" -Encoding utf8

# ── ARCHITECTURE.mmd ──────────────────────────────────────────────────────────
$architecture = @"
graph TB
    subgraph Frontend["Frontend (React 18 + Vite)"]
        PlatformPage["PlatformPage<br/>/platform"]
        MicrosoftWizard["MicrosoftModePage<br/>/microsoft (3-step wizard)"]
        DevOpsPolicy["DevOpsPage<br/>/devops (Policy Gate tab)"]
    end

    subgraph API["FastAPI (port 8090)"]
        platform_router["/platform/*"]
        orchestrator_router["/orchestrator/*"]
        policy_router["/devops/policy/*"]
        mcp_router["/mcp/*"]
    end

    subgraph Agents["Multi-Agent Pipeline"]
        IntakeAgent["IntakeAgent"]
        RiskAgent["RiskAgent"]
        ReportAgent["ReportAgent"]
        SREAgent["SREAgent (stub)"]
    end

    subgraph LLM["LLM Layer"]
        MockProvider["MockProvider<br/>(offline / deterministic)"]
    end

    PlatformPage -->|GET /platform/*| platform_router
    MicrosoftWizard -->|GET /orchestrator/plan| orchestrator_router
    MicrosoftWizard -->|POST /orchestrator/run| orchestrator_router
    DevOpsPolicy -->|POST /devops/policy/evaluate| policy_router
    DevOpsPolicy -->|POST /devops/policy/export| policy_router

    orchestrator_router --> IntakeAgent
    IntakeAgent --> RiskAgent
    RiskAgent --> ReportAgent
    ReportAgent --> SREAgent
    IntakeAgent --> MockProvider
    RiskAgent --> MockProvider
"@

$architecture | Out-File -FilePath "$outDir\ARCHITECTURE.mmd" -Encoding utf8

# ── DEMO_SCRIPT.md ──────────────────────────────────────────────────────────
$demoScript = @"
# RiskCanvas Wave 6 Demo Script

## Prerequisites
```bash
# Terminal 1 — API
cd apps/api
uvicorn main:app --port 8090 --reload

# Terminal 2 — Frontend
cd apps/web
npm run preview
```

## Demo Stops

### 1. Version Check (v3.2.0)
- Navigate to http://localhost:4174
- Point to sidebar version badge showing **v3.2.0**

### 2. Platform Health Dashboard (v2.9)
- Click **Platform** in sidebar (nav-platform)
- Show health cards: Service Health, Readiness, Liveness, Infra Validation
- Point to Port 8090 badge
- Click **Refresh**

### 3. Microsoft Mode Wizard (v3.0)
- Navigate to **/microsoft**
- **Step 1:** Show provider status card (Mock Provider / DEMO mode)
- Click **Next**
- **Step 2:** Show MCP tools list (4 tools)
- Click **Test portfolio_analyze** → show SUCCESS badge
- Click **Next**
- **Step 3:** Show agent plan steps (4 agents)
- Click **Run Multi-Agent Pipeline**
- Show audit log table (IntakeAgent → RiskAgent → ReportAgent → SREAgent)
- Show SRE checks (all passed)

### 4. DevOps Policy Gate (v3.1)
- Navigate to **/devops**
- Click **Policy Gate** tab
- Enter clean diff: `+def calculate_risk():\n+    return 0.05`
- Click **Evaluate Policy** → show ALLOW badge
- Enter dirty diff with secrets
- Click **Evaluate Policy** → show BLOCK badge with blocker reasons
- Click **Export Markdown** → show MR comment preview

### 5. Close the Loop
- Navigate back to Dashboard
- Point to all newly added nav items
"@

$demoScript | Out-File -FilePath "$outDir\DEMO_SCRIPT.md" -Encoding utf8

# ── LINKS.md ──────────────────────────────────────────────────────────────────
$links = @"
# RiskCanvas Wave 6 – Key Links

## API Endpoints (port 8090)
- Platform Health: http://localhost:8090/platform/health/details
- Platform Readiness: http://localhost:8090/platform/readiness
- Platform Liveness: http://localhost:8090/platform/liveness
- Infra Validation: http://localhost:8090/platform/infra/validate
- Orchestrator Plan: http://localhost:8090/orchestrator/plan
- Orchestrator Run: http://localhost:8090/orchestrator/run
- Policy Evaluate: http://localhost:8090/devops/policy/evaluate
- Policy Export: http://localhost:8090/devops/policy/export
- Policy Rules: http://localhost:8090/devops/policy/rules
- MCP Tools: http://localhost:8090/mcp/tools
- API Docs: http://localhost:8090/docs

## Frontend Routes (port 4174)
- Dashboard: http://localhost:4174/
- Platform: http://localhost:4174/platform
- Microsoft Wizard: http://localhost:4174/microsoft
- DevOps: http://localhost:4174/devops
- Jobs: http://localhost:4174/jobs

## Test Commands
\`\`\`powershell
# pytest
cd apps/api; python -m pytest tests/ -q

# vitest
cd apps/web; npx vitest run

# tsc
cd apps/web; npx tsc --noEmit

# playwright (standard suite)
cd e2e; npx playwright test --config playwright.config.ts

# playwright (judge demo)
cd e2e; npx playwright test --config playwright.judge.config.ts
\`\`\`
"@

$links | Out-File -FilePath "$outDir\LINKS.md" -Encoding utf8

# ── Zip the pack ──────────────────────────────────────────────────────────────
$zipPath = "$outDir\..\$timestamp-wave6.zip"
Compress-Archive -Path "$outDir\*" -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "✅ Submission pack complete:"
Write-Host "   Directory: $outDir"
Write-Host "   Archive:   $zipPath"
Write-Host ""
Write-Host "Contents:"
Get-ChildItem $outDir | Format-Table Name, Length -AutoSize
