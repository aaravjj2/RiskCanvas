#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run Wave 6 proof pack: pytest + vitest + tsc + vite build
.DESCRIPTION
    Executes the full test matrix for Wave 6 (v2.9 → v3.2).
    Output is saved to artifacts/proof/<timestamp>-wave6-v2.9-3.2/
    All suites must pass with 0 failures, 0 skips.
#>

$ErrorActionPreference = "Stop"
$timestamp = (Get-Date -Format "yyyyMMdd-HHmmss")
$proofDir = "$PSScriptRoot\..\..\artifacts\proof\$timestamp-wave6-v2.9-3.2"
New-Item -ItemType Directory -Path $proofDir -Force | Out-Null
$repoRoot = "$PSScriptRoot\..\.."

$failures = 0
$results = @()

function Run-Step {
    param([string]$Name, [string]$WorkDir, [string]$Command)
    Write-Host ""
    Write-Host "━━━ $Name ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    $logFile = "$proofDir\$($Name -replace '\s+','-').log"
    Push-Location $WorkDir
    try {
        $output = Invoke-Expression $Command 2>&1 | Tee-Object -FilePath $logFile
        $code = $LASTEXITCODE
        if ($code -ne 0) {
            Write-Host "  ❌ FAILED (exit $code)" -ForegroundColor Red
            $script:failures++
            $script:results += [PSCustomObject]@{ Step=$Name; Status="FAILED"; Code=$code }
        } else {
            Write-Host "  ✅ PASSED" -ForegroundColor Green
            $script:results += [PSCustomObject]@{ Step=$Name; Status="PASSED"; Code=0 }
        }
    } finally {
        Pop-Location
    }
}

# ── 1. pytest ─────────────────────────────────────────────────────────────────
Run-Step "pytest" "$repoRoot\apps\api" "python -m pytest tests/ -q --tb=short 2>&1"

# ── 2. vitest ─────────────────────────────────────────────────────────────────
Run-Step "vitest" "$repoRoot\apps\web" "npx vitest run 2>&1"

# ── 3. tsc ────────────────────────────────────────────────────────────────────
Run-Step "tsc" "$repoRoot\apps\web" "npx tsc --noEmit 2>&1"

# ── 4. vite build ─────────────────────────────────────────────────────────────
Run-Step "vite-build" "$repoRoot\apps\web" "npm run build 2>&1"

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "Wave 6 Proof Pack Summary"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$results | Format-Table Step, Status -AutoSize

$summaryPath = "$proofDir\SUMMARY.md"
$summaryContent = @"
# Wave 6 Proof Pack Summary
**Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Result:** $(if ($failures -eq 0) { "✅ ALL PASSED" } else { "❌ $failures FAILED" })

## Test Results
| Step | Status |
|------|--------|
$(($results | ForEach-Object { "| $($_.Step) | $($_.Status) |" }) -join "`n")

## Proof directory
$proofDir
"@
$summaryContent | Out-File -FilePath $summaryPath -Encoding utf8

Write-Host ""
Write-Host "Proof artifacts saved to: $proofDir"

if ($failures -gt 0) {
    Write-Host ""
    Write-Host "❌ $failures step(s) failed. Check logs in $proofDir" -ForegroundColor Red
    exit 1
} else {
    Write-Host ""
    Write-Host "✅ All steps passed." -ForegroundColor Green
    exit 0
}
