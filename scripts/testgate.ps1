$ErrorActionPreference = "Stop"

function Run($name, $cmd) {
  Write-Host "`n=== $name ==="
  Write-Host $cmd
  & powershell -NoProfile -Command $cmd
  if ($LASTEXITCODE -ne 0) { throw "$name failed ($LASTEXITCODE)" }
}

# Hard fail if scaffold missing (this forces M0.1 to create the structure)
if (!(Test-Path ".\apps\web\package.json")) { throw "Missing apps/web/package.json" }
if (!(Test-Path ".\apps\api")) { throw "Missing apps/api" }
if (!(Test-Path ".\e2e")) { throw "Missing e2e" }

# Web
Run "Web: install" "cd apps/web; if (Test-Path package-lock.json) { npm ci } else { npm install }"
Run "Web: typecheck" "cd apps/web; npm run -s typecheck"
Run "Web: unit tests" "cd apps/web; npm test --silent"

# API
Run "API: deps" "cd apps/api; python -m pip install -r requirements.txt"
Run "API: unit tests" "cd apps/api; pytest -q"

# E2E
Run "E2E: install" "cd e2e; if (Test-Path package-lock.json) { npm ci } else { npm install }"
Run "E2E: playwright" "cd e2e; npx playwright test --retries=0 --workers=1"

Write-Host "`nALL GATES PASSED"
