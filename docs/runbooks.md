# RiskCanvas Runbooks

## 1. Local Development

### Start API server
```bash
cd apps/api
source ../../.venv/bin/activate   # Linux/Mac
# or: ..\..\venv\Scripts\activate  # Windows
uvicorn main:app --reload --port 8090
```

### Start web dev server
```bash
npm --prefix apps/web run dev
```

### Run all tests
```bash
# Python (API + engine)
cd apps/api && python -m pytest -q
cd packages/engine && python -m pytest tests/ -v

# TypeScript
npx tsc -p apps/web/tsconfig.json --noEmit
npx vitest run

# E2E
npx playwright test --config=e2e/playwright.config.ts
```

---

## 2. Deployment

### Deploy to DigitalOcean
See [deploy/digitalocean/DEPLOY.md](../deploy/digitalocean/DEPLOY.md).

### Quick Commands
```bash
cd deploy/digitalocean
docker compose up -d --build      # Start
docker compose down               # Stop
docker compose logs -f api        # API logs
docker compose logs -f web        # Web logs
docker compose restart api        # Restart API only
```

---

## 3. Incident Response

### API returns 500

1. Check API logs: `docker compose logs api --tail=100`
2. Look for Python tracebacks
3. Common causes:
   - Engine path not found → check `PYTHONPATH` in Dockerfile
   - Missing fixture file → verify `/app/fixtures/` in container
4. Restart: `docker compose restart api`

### Non-Determinism Detected

1. Run determinism check: `curl -X POST http://localhost:8090/determinism/check`
2. Check which computation failed in the `checks` array
3. Compare `hash` values across environments
4. Common causes:
   - Platform-dependent floating point (unlikely with 8-digit precision)
   - Different Python versions
5. Resolution: Pin Python version, verify `NUMERIC_PRECISION` unchanged

### High Memory Usage

1. Check: `docker stats`
2. Monte Carlo VaR is capped at 100,000 paths
3. If memory grows indefinitely, likely a leak in long-running uvicorn
4. Resolution: `docker compose restart api`

### Web App Shows DEMO Data Only

1. This is expected when `DEMO_MODE=true` or API is unreachable
2. Check API connectivity: `curl http://localhost:8090/health`
3. Check browser console for fetch errors
4. Verify nginx proxy config routes `/api/` correctly

---

## 4. GitLab CI

### Pipeline Fails

1. Check which stage failed in GitLab CI/CD → Pipelines
2. **lint:python** — Run `ruff check apps/api/` locally
3. **test:pytest** — Run `cd apps/api && python -m pytest -q`
4. **test:vitest** — Run `npx vitest run`
5. **test:playwright** — Run `npx playwright test`; check artifacts for screenshots

### Mirror to GitLab

```powershell
.\scripts\gitlab-mirror.ps1 -GitLabUrl "https://gitlab.com/org/riskcanvas.git"
```

---

## 5. Common Tasks

### Add a New API Endpoint

1. Define Pydantic models in `apps/api/schemas.py`
2. Add route in `apps/api/main.py`
3. Add tests in `apps/api/tests/`
4. Update `docs/api.md`
5. Run full test suite

### Update Engine Computation

1. Modify files in `packages/engine/src/`
2. Run `packages/engine/tests/test_determinism.py` to verify determinism
3. Run `packages/engine/tests/test_edge_cases.py` for boundary conditions
4. Run full pytest suite
5. Bump `ENGINE_VERSION` in `packages/engine/src/__init__.py` and `apps/api/main.py`

### Generate Proof Pack

```powershell
.\scripts\proofpack.ps1
```
