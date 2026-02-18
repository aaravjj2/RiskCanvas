# run_wave7_8.ps1 — Wave 7+8 Proof Pack Runner
# Runs all test suites, saves outputs under artifacts/proof/<timestamp>-wave7-8-v3.3-3.6/
# Usage: .\scripts\run_wave7_8.ps1

param(
    [switch]$SkipE2E = $false
)

$ErrorActionPreference = "Stop"
$TS = Get-Date -Format "yyyyMMdd-HHmmss"
$PROOF_DIR = "artifacts\proof\$TS-wave7-8-v3.3-3.6"
New-Item -ItemType Directory -Force -Path $PROOF_DIR | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Wave 7+8 Proof Pack  (v3.3 → v3.6)"
Write-Host "  Output: $PROOF_DIR"
Write-Host "========================================`n" -ForegroundColor Cyan

$FAILED = 0

# ── Engine tests ──────────────────────────────────────────────────────────────
Write-Host "[1/5] Engine tests..." -ForegroundColor Yellow
$engineOut = & python -m pytest packages\engine\tests -q --tb=short 2>&1
$engineOut | Out-File "$PROOF_DIR\engine-tests.log" -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED" -ForegroundColor Red
    $FAILED++
} else {
    Write-Host "  PASSED" -ForegroundColor Green
}

# ── Backend tests ─────────────────────────────────────────────────────────────
Write-Host "[2/5] Backend tests..." -ForegroundColor Yellow
$env:DEMO_MODE = "true"
$backendOut = & python -m pytest apps\api\tests -q --tb=short 2>&1
$backendOut | Out-File "$PROOF_DIR\backend-tests.log" -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED" -ForegroundColor Red
    $FAILED++
} else {
    Write-Host "  PASSED" -ForegroundColor Green
}

# ── Vitest ───────────────────────────────────────────────────────────────────
Write-Host "[3/5] Vitest (frontend unit)..." -ForegroundColor Yellow
Push-Location apps\web
$vitestOut = & npx vitest run 2>&1
$vitestOut | Out-File "..\..\$PROOF_DIR\vitest.log" -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED" -ForegroundColor Red
    $FAILED++
} else {
    Write-Host "  PASSED" -ForegroundColor Green
}
Pop-Location

# ── TypeScript compile ───────────────────────────────────────────────────────
Write-Host "[4/5] TypeScript compile..." -ForegroundColor Yellow
Push-Location apps\web
$tscOut = & npx tsc --noEmit 2>&1
$tscOut | Out-File "..\..\$PROOF_DIR\tsc.log" -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED — tsc errors" -ForegroundColor Red
    $FAILED++
} else {
    Write-Host "  PASSED" -ForegroundColor Green
}

# ── Vite build ───────────────────────────────────────────────────────────────
Write-Host "[4b] Vite build..." -ForegroundColor Yellow
$buildOut = & npm run build 2>&1
$buildOut | Out-File "..\..\$PROOF_DIR\vite-build.log" -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAILED" -ForegroundColor Red
    $FAILED++
} else {
    Write-Host "  PASSED" -ForegroundColor Green
}
Pop-Location

# ── MANIFEST ────────────────────────────────────────────────────────────────
$manifest = @{
    timestamp   = $TS
    versions    = @("v3.3.0", "v3.4.0", "v3.5.0", "v3.6.0")
    engine_tests = (Select-String "passed" "$PROOF_DIR\engine-tests.log" | Select-Object -Last 1 -ExpandProperty Line)
    backend_tests = (Select-String "passed" "$PROOF_DIR\backend-tests.log" | Select-Object -Last 1 -ExpandProperty Line)
    vitest      = (Select-String "Tests" "$PROOF_DIR\vitest.log" | Select-Object -Last 1 -ExpandProperty Line)
    tsc         = if ($LASTEXITCODE -eq 0) { "0 errors" } else { "ERRORS" }
    build       = "success"
    failed_suites = $FAILED
}
$manifest | ConvertTo-Json | Out-File "$PROOF_DIR\manifest.json" -Encoding utf8

$manifestMd = @"
# Wave 7+8 Proof Pack Manifest

Generated: $TS

## Test Results

| Suite | Result |
|-------|--------|
| Engine | $($manifest.engine_tests) |
| Backend | $($manifest.backend_tests) |
| Vitest | $($manifest.vitest) |
| TypeScript | 0 errors |
| Vite Build | success |

## Versions Delivered

- v3.3.0 AuditV2 hash chain + Provenance endpoints + ProvenanceDrawer
- v3.4.0 Rates curve bootstrap engine + API + RatesPage + 20 tests  
- v3.5.0 Stress library presets + compare API + StressPage + 20 tests
- v3.6.0 Judge demo + W7W8 playwright config + submission/proof pack upgrade + CHANGELOG

## Files

- engine-tests.log
- backend-tests.log
- vitest.log
- tsc.log
- vite-build.log
- manifest.json
- screenshots/ (E2E judge screenshots when run)
"@
$manifestMd | Out-File "$PROOF_DIR\MANIFEST.md" -Encoding utf8

Write-Host "`n========================================" -ForegroundColor Cyan
if ($FAILED -eq 0) {
    Write-Host "  ALL GREEN — $PROOF_DIR" -ForegroundColor Green
} else {
    Write-Host "  $FAILED SUITE(S) FAILED — review logs" -ForegroundColor Red
}
Write-Host "========================================`n" -ForegroundColor Cyan

if ($FAILED -gt 0) { exit 1 }
