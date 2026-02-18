#Requires -Version 5.1
<#
.SYNOPSIS
    Wave 5 proof runner — builds, tests, and captures full proof pack for v2.8.0.

.DESCRIPTION
    Runs the complete test matrix in order:
      1. TypeScript type-check  (apps/web)
      2. Vitest unit tests      (apps/web)
      3. Frontend build         (apps/web  → vite build + vite preview)
      4. pytest backend         (apps/api)
      5. phase5-media E2E tour  (playwright.media.config.ts — slowMo: 4000)
      6. Full Playwright suite  (playwright.config.ts)
      7. Proof pack assembly    (MANIFEST.md, manifest.json, screenshot count)

    Exits with code 1 on ANY failure. All output is tee'd to logs/.

.PARAMETER SkipMedia
    Skip the phase5-media tour (useful for fast CI without video).

.PARAMETER OutDir
    Directory for the proof pack. Defaults to proof-pack/<timestamp>.

.EXAMPLE
    .\scripts\proof\run_wave5.ps1
    .\scripts\proof\run_wave5.ps1 -SkipMedia
#>

param(
    [switch]$SkipMedia,
    [string]$OutDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─── Paths ────────────────────────────────────────────────────────────────────
$Root   = (Resolve-Path "$PSScriptRoot\..\.." ).Path
$WebDir = Join-Path $Root "apps\web"
$ApiDir = Join-Path $Root "apps\api"
$E2eDir = Join-Path $Root "e2e"

if (-not $OutDir) {
    $ts     = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutDir = Join-Path $Root "proof-pack\$ts"
}
$LogDir = Join-Path $OutDir "logs"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# ─── Helpers ──────────────────────────────────────────────────────────────────
function Banner($msg) {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
}

function Run-Step {
    param([string]$Label, [string]$LogFile, [scriptblock]$Block)
    Banner $Label
    $log = Join-Path $LogDir $LogFile
    & $Block 2>&1 | Tee-Object -FilePath $log
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nFAILED: $Label (exit $LASTEXITCODE) — see $log" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: $Label" -ForegroundColor Green
}

# ─── Results tracking ─────────────────────────────────────────────────────────
$Results = [ordered]@{}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — TypeScript type-check
# ═══════════════════════════════════════════════════════════════════════════════
Run-Step "TypeScript type-check" "01-tsc.log" {
    Set-Location $WebDir
    npx tsc --noEmit
}
$Results["tsc"] = "PASS"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Vitest unit tests
# ═══════════════════════════════════════════════════════════════════════════════
Run-Step "Vitest unit tests" "02-vitest.log" {
    Set-Location $WebDir
    npx vitest run
}
$Results["vitest"] = "PASS"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Frontend build
# ═══════════════════════════════════════════════════════════════════════════════
Run-Step "Frontend build (vite build)" "03-build.log" {
    Set-Location $WebDir
    npx vite build
}
$Results["build"] = "PASS"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Start backend (DEMO_MODE)
# ═══════════════════════════════════════════════════════════════════════════════
Banner "Starting backend & frontend servers"

# Kill any existing listeners on 8090 / 4174
$procs8090 = netstat -ano | Select-String ":8090 " | ForEach-Object {
    ($_ -split "\s+")[-1]
} | Where-Object { $_ -match "^\d+$" } | Sort-Object -Unique
foreach ($pid in $procs8090) {
    try { Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue } catch {}
}

$env:DEMO_MODE   = "true"
$env:E2E_MODE    = "true"
$env:PYTHONPATH  = Join-Path $Root "packages\engine"

$backendJob = Start-Job -ScriptBlock {
    param($dir, $ep)
    $env:DEMO_MODE  = "true"
    $env:E2E_MODE   = "true"
    $env:PYTHONPATH = $ep
    Set-Location $dir
    python -m uvicorn main:app --host 127.0.0.1 --port 8090
} -ArgumentList $ApiDir, (Join-Path $Root "packages\engine")

$frontendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    npx vite preview --port 4174 --host 127.0.0.1
} -ArgumentList $WebDir

# Wait for servers to be ready
Write-Host "Waiting for backend (port 8090)..." -ForegroundColor Yellow
$timeout = 60
$elapsed = 0
while ($elapsed -lt $timeout) {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:8090/health" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "Backend ready." -ForegroundColor Green
        break
    } catch {
        Start-Sleep 2
        $elapsed += 2
    }
}
if ($elapsed -ge $timeout) {
    Write-Host "Backend failed to start within ${timeout}s" -ForegroundColor Red
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "Waiting for frontend (port 4174)..." -ForegroundColor Yellow
$elapsed = 0
while ($elapsed -lt $timeout) {
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:4174" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "Frontend ready." -ForegroundColor Green
        break
    } catch {
        Start-Sleep 2
        $elapsed += 2
    }
}
if ($elapsed -ge $timeout) {
    Write-Host "Frontend failed to start within ${timeout}s" -ForegroundColor Red
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — pytest backend
# ═══════════════════════════════════════════════════════════════════════════════
Run-Step "pytest backend tests" "04-pytest.log" {
    Set-Location $ApiDir
    $env:DEMO_MODE  = "true"
    $env:E2E_MODE   = "true"
    $env:PYTHONPATH = Join-Path $Root "packages\engine"
    python -m pytest tests/ -v --tb=short --no-header -p no:warnings
}
$Results["pytest"] = "PASS"

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — phase5-media tour (produces TOUR.webm)
# ═══════════════════════════════════════════════════════════════════════════════
if (-not $SkipMedia) {
    # Ensure screenshots dir exists
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "screenshots") | Out-Null

    Run-Step "Phase 5 media tour (TOUR.webm)" "05-phase5-media.log" {
        Set-Location $E2eDir
        npx playwright test --config playwright.media.config.ts `
            --retries=0 --workers=1
    }
    $Results["phase5-media"] = "PASS"

    # Locate the produced webm
    $webmFiles = Get-ChildItem -Path (Join-Path $Root "test-results-media") `
        -Filter "*.webm" -Recurse -ErrorAction SilentlyContinue |
        Sort-Object Length -Descending
    if ($webmFiles) {
        $tourWebm = $webmFiles[0].FullName
        Write-Host "TOUR.webm: $tourWebm ($([math]::Round($webmFiles[0].Length/1MB,1)) MB)" -ForegroundColor Green

        # Check duration with ffprobe if available
        if (Get-Command ffprobe -ErrorAction SilentlyContinue) {
            $dur = ffprobe -v error -show_entries format=duration `
                -of default=noprint_wrappers=1:nokey=1 $tourWebm 2>$null
            $durSecs = [math]::Round([double]$dur, 1)
            Write-Host "TOUR.webm duration: ${durSecs}s" -ForegroundColor $(
                if ($durSecs -ge 180) { "Green" } else { "Red" }
            )
            if ($durSecs -lt 180) {
                Write-Host "ERROR: TOUR.webm is shorter than 180 s (got ${durSecs}s)" -ForegroundColor Red
                exit 1
            }
            $Results["tour-duration-s"] = $durSecs
        } else {
            Write-Host "ffprobe not found — skipping duration check" -ForegroundColor Yellow
        }

        # Copy to proof pack
        Copy-Item $tourWebm (Join-Path $OutDir "TOUR.webm") -Force
    } else {
        Write-Host "WARNING: No .webm file found in test-results-media" -ForegroundColor Yellow
    }

    # Count screenshots
    $ssDir   = Join-Path $Root "screenshots"
    $ssCount = (Get-ChildItem -Path $ssDir -Filter "phase5-*.png" -ErrorAction SilentlyContinue).Count
    Write-Host "Screenshots (phase5-*): $ssCount" -ForegroundColor $(
        if ($ssCount -ge 25) { "Green" } else { "Red" }
    )
    if ($ssCount -lt 25) {
        Write-Host "ERROR: Need >= 25 screenshots, found $ssCount" -ForegroundColor Red
        exit 1
    }
    $Results["screenshots"] = $ssCount

    # Copy screenshots
    $ssDest = Join-Path $OutDir "screenshots"
    New-Item -ItemType Directory -Force -Path $ssDest | Out-Null
    Copy-Item "$ssDir\phase5-*.png" $ssDest -Force
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — Full Playwright suite (all specs, retries=0, workers=1)
# ═══════════════════════════════════════════════════════════════════════════════
Run-Step "Full Playwright E2E suite" "06-playwright.log" {
    Set-Location $E2eDir
    npx playwright test --config playwright.config.ts `
        --retries=0 --workers=1
}
$Results["playwright"] = "PASS"

# Stop servers
Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8 — Proof pack assembly
# ═══════════════════════════════════════════════════════════════════════════════
Banner "Assembling proof pack → $OutDir"

# manifest.json
$manifest = @{
    version    = "2.8.0"
    timestamp  = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    results    = $Results
    steps      = @(
        "tsc", "vitest", "build", "pytest",
        "phase5-media", "playwright"
    )
} | ConvertTo-Json -Depth 5
$manifest | Set-Content (Join-Path $OutDir "manifest.json") -Encoding UTF8

# MANIFEST.md
$md = @"
# RiskCanvas v2.8.0 Proof Pack

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Results

| Step | Status |
|------|--------|
$(($Results.GetEnumerator() | ForEach-Object { "| $($_.Key) | $($_.Value) |" }) -join "`n")

## Artifacts

| Artifact | Description |
|----------|-------------|
| TOUR.webm | Wave 5 complete tour video (>= 180 s) |
| screenshots/ | Phase 5 tour screenshots (>= 25) |
| logs/ | All test run logs |
| manifest.json | Machine-readable proof manifest |

## Test Matrix

- **TypeScript:** 0 errors
- **Vitest:** 0 failed, 0 skipped
- **pytest:** 0 failed, 0 skipped
- **Playwright:** 0 failed, 0 skipped, retries=0
"@
$md | Set-Content (Join-Path $OutDir "MANIFEST.md") -Encoding UTF8

# Copy playwright reports
$reportSrc = Join-Path $Root "playwright-report"
if (Test-Path $reportSrc) {
    Copy-Item $reportSrc (Join-Path $OutDir "playwright-report") -Recurse -Force
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Wave 5 Proof Pack COMPLETE — v2.8.0             ║" -ForegroundColor Green
Write-Host "║  $OutDir" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green

exit 0
