# RiskCanvas Threat Model

## 1. Overview

RiskCanvas is a portfolio risk analysis platform. This document identifies
potential threats, their impact, and mitigations in place.

## 2. Trust Boundaries

```
┌─────────────────────────────────────────────┐
│  Browser (untrusted)                        │
│  ├── React SPA                              │
│  └── User input (portfolio data)            │
├─────────────────────────────────────────────┤
│  Reverse Proxy (nginx)                      │
├─────────────────────────────────────────────┤
│  API Server (FastAPI)  ◄── Trust Boundary   │
│  ├── Input validation (Pydantic)            │
│  ├── Error taxonomy (errors.py)             │
│  └── CORS middleware                        │
├─────────────────────────────────────────────┤
│  Engine (pure computation, no I/O)          │
│  └── Deterministic, no network access       │
└─────────────────────────────────────────────┘
```

## 3. Threat Catalog

### T1 — Malicious Portfolio Input

| Property | Value |
|----------|-------|
| **STRIDE** | Tampering |
| **Risk** | Medium |
| **Attack** | Crafted JSON with extreme values (e.g., `sigma=1e308`) to cause NaN/Inf or denial-of-service |
| **Mitigation** | Pydantic validation on all request models; guardrails in `monte_carlo_var` (max_paths=100000, seed range check); engine returns `round_to_precision()` values |

### T2 — Non-Deterministic Output

| Property | Value |
|----------|-------|
| **STRIDE** | Information Disclosure / Repudiation |
| **Risk** | High (for compliance) |
| **Attack** | Floating-point non-determinism across runs leading to different risk numbers |
| **Mitigation** | `NUMERIC_PRECISION=8`, `FIXED_SEED=42`, determinism check endpoint (`/determinism/check`), determinism test suite (`test_determinism_v1.py`) |

### T3 — API Key Leakage

| Property | Value |
|----------|-------|
| **STRIDE** | Information Disclosure |
| **Risk** | Low (DEMO_MODE default) |
| **Attack** | Secrets exposed in logs, error messages, or source code |
| **Mitigation** | `DEMO_MODE=true` by default (no real keys needed); `.env.template` has placeholders only; no secrets logged |

### T4 — CORS Misconfiguration

| Property | Value |
|----------|-------|
| **STRIDE** | Elevation of Privilege |
| **Risk** | Low |
| **Attack** | Cross-origin requests from malicious sites |
| **Mitigation** | CORS `allow_origins=["*"]` is acceptable for DEMO_MODE. Production should restrict to specific domains. |

### T5 — Denial of Service

| Property | Value |
|----------|-------|
| **STRIDE** | Denial of Service |
| **Risk** | Medium |
| **Attack** | Flood of expensive computation requests (e.g., large monte carlo) |
| **Mitigation** | `monte_carlo_var` capped at 100,000 paths; no unbounded loops in engine; Docker healthcheck for restart |

### T6 — Container Escape

| Property | Value |
|----------|-------|
| **STRIDE** | Elevation of Privilege |
| **Risk** | Low |
| **Attack** | Exploit in Docker runtime |
| **Mitigation** | Minimal base images (`python:3.11-slim`, `nginx:alpine`); no root processes in containers; no privileged mode |

## 4. Risk Matrix

| Threat | Likelihood | Impact | Overall |
|--------|-----------|--------|---------|
| T1 Malicious Input | Medium | Medium | **Medium** |
| T2 Non-Determinism | Low | High | **Medium** |
| T3 API Key Leak | Low | Medium | **Low** |
| T4 CORS Misconfig | Low | Low | **Low** |
| T5 DoS | Medium | Medium | **Medium** |
| T6 Container Escape | Low | High | **Low** |

## 5. Recommendations

1. **Production**: Restrict CORS origins to specific domains
2. **Production**: Add rate limiting middleware
3. **Production**: Use non-root Docker user
4. **CI**: Run determinism check in every pipeline
5. **Monitoring**: Alert on non-determinism check failures
