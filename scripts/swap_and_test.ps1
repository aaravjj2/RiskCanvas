# PowerShell Script: Swap Files and Run Tests
# RiskCanvas Phase 0 v0.8 - Full Test Gate Execution

Write-Host "=== RiskCanvas Phase 0 v0.8 - File Swap and Test Gate ===" -ForegroundColor Cyan

# Define root
$ROOT = "c:\RiskCanvas\RiskCanvas"

# Step 1: Backup old files
Write-Host "`n[1/8] Backing up old files..." -ForegroundColor Yellow
Copy-Item "$ROOT\apps\web\src\App.tsx" "$ROOT\apps\web\src\App_old.tsx" -Force
Copy-Item "$ROOT\apps\web\src\App.css" "$ROOT\apps\web\src\App_old.css" -Force
Copy-Item "$ROOT\apps\api\main.py" "$ROOT\apps\api\main_old.py" -Force
Copy-Item "$ROOT\e2e\playwright.config.ts" "$ROOT\e2e\playwright_old.config.ts" -Force
Copy-Item "$ROOT\e2e\test.spec.ts" "$ROOT\e2e\test_old.spec.ts" -Force
Write-Host "Backups created" -ForegroundColor Green

# Step 2: Swap frontend files
Write-Host "`n[2/8] Swapping frontend files..." -ForegroundColor Yellow
Copy-Item "$ROOT\apps\web\src\App_new.tsx" "$ROOT\apps\web\src\App.tsx" -Force
Copy-Item "$ROOT\apps\web\src\App_new.css" "$ROOT\apps\web\src\App.css" -Force
Write-Host "Frontend files swapped" -ForegroundColor Green

# Step 3: Swap API main.py
Write-Host "`n[3/8] Swapping API main.py..." -ForegroundColor Yellow
Copy-Item "$ROOT\apps\api\main_new.py" "$ROOT\apps\api\main.py" -Force
Write-Host "API main.py swapped" -ForegroundColor Green

# Step 4: Swap E2E test files
Write-Host "`n[4/8] Swapping E2E test files..." -ForegroundColor Yellow
Copy-Item "$ROOT\e2e\playwright_new.config.ts" "$ROOT\e2e\playwright.config.ts" -Force
Copy-Item "$ROOT\e2e\test_new.spec.ts" "$ROOT\e2e\test.spec.ts" -Force
Write-Host "E2E files swapped" -ForegroundColor Green

# Step 5: Install dependencies
Write-Host "`n[5/8] Installing dependencies..." -ForegroundColor Yellow

Write-Host "Installing Python packages..." -ForegroundColor White
Set-Location "$ROOT\apps\api"
python -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python install failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Installing frontend packages..." -ForegroundColor White
Set-Location "$ROOT\apps\web"
npm install --silent
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend npm install failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Installing E2E packages..." -ForegroundColor White
Set-Location "$ROOT\e2e"
npm install --silent
if ($LASTEXITCODE -ne 0) {
    Write-Host "E2E npm install failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Dependencies installed" -ForegroundColor Green

# Step 6: Run TypeScript Check
Write-Host "`n[6/8] Running TypeScript check (tsc)..." -ForegroundColor Yellow
Set-Location "$ROOT\apps\web"
npm run typecheck
$tscExitCode = $LASTEXITCODE
if ($tscExitCode -eq 0) {
    Write-Host "TypeScript: PASS (0 errors)" -ForegroundColor Green
} else {
    Write-Host "TypeScript: FAIL ($tscExitCode errors)" -ForegroundColor Red
}

# Step 7: Run Vitest
Write-Host "`n[7/8] Running Vitest..." -ForegroundColor Yellow
Set-Location "$ROOT\apps\web"
npm run test
$vitestExitCode = $LASTEXITCODE
if ($vitestExitCode -eq 0) {
    Write-Host "Vitest: PASS" -ForegroundColor Green
} else {
    Write-Host "Vitest: FAIL" -ForegroundColor Red
}

# Step 8: Run Pytest
Write-Host "`n[8/8] Running Pytest..." -ForegroundColor Yellow
Set-Location "$ROOT\apps\api"
pytest tests/ -v --tb=short
$pytestExitCode = $LASTEXITCODE
if ($pytestExitCode -eq 0) {
    Write-Host "Pytest: PASS" -ForegroundColor Green
} else {
    Write-Host "Pytest: FAIL" -ForegroundColor Red
}

# Summary
Write-Host "`n=== TEST GATE SUMMARY ===" -ForegroundColor Cyan
Write-Host "TypeScript (tsc): $(if ($tscExitCode -eq 0) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($tscExitCode -eq 0) { 'Green' } else { 'Red' })
Write-Host "Vitest:           $(if ($vitestExitCode -eq 0) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($vitestExitCode -eq 0) { 'Green' } else { 'Red' })
Write-Host "Pytest:           $(if ($pytestExitCode -eq 0) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($pytestExitCode -eq 0) { 'Green' } else { 'Red' })

$allPassed = ($tscExitCode -eq 0) -and ($vitestExitCode -eq 0) -and ($pytestExitCode -eq 0)

if ($allPassed) {
    Write-Host "`nALL GATES PASSED! ✓" -ForegroundColor Green
    Write-Host "Ready for Playwright E2E tests" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "`nSOME GATES FAILED! ✗" -ForegroundColor Red
    Write-Host "Fix errors before running E2E" -ForegroundColor Yellow
    exit 1
}
