$ErrorActionPreference = "Stop"

function Run-Step([string]$name, [scriptblock]$cmd) {
  Write-Host "`n=== $name ==="
  try {
    & $cmd
    $exit = $global:LASTEXITCODE
    if ($null -ne $exit -and $exit -ne 0) {
      throw "$name failed ($exit)"
    }
  } catch {
    throw "$name failed: $($_.Exception.Message)"
  }
}

Run-Step "Web: typecheck" { npm --prefix apps/web run -s typecheck }
Run-Step "Web: test"      { npm --prefix apps/web test --silent }

if (Test-Path ".\apps\api") {
  if (Test-Path ".\apps\api\.venv\Scripts\python.exe") {
    Run-Step "API: pytest" { Push-Location .\apps\api; .\.venv\Scripts\python -m pytest -q; Pop-Location }
  } else {
    Write-Host "`n(skipping API pytest: apps/api/.venv not found)"
  }
}

function Run-E2E-With-Retry([int]$retries = 1) {
  $cmd = { npx playwright test --config .\e2e\playwright.config.ts }
  for ($i = 0; $i -le $retries; $i++) {
    try {
      Run-Step "E2E: playwright" $cmd
      return
    } catch {
      Write-Host "E2E attempt $($i + 1) failed: $($_.Exception.Message)"
      if ($i -lt $retries) {
        Write-Host "Collecting diagnostics before retry..."
        if (Test-Path ".\apps\web\src\index.css") {
          Write-Host "Found apps/web/src/index.css"
        } else {
          Write-Host "Missing apps/web/src/index.css"
        }
        Write-Host "Listing apps/web/src/"
        Get-ChildItem -Path .\apps\web\src -Force | ForEach-Object { Write-Host $_.Name }
        Start-Sleep -Seconds 2
        Write-Host "Retrying E2E..."
      } else {
        throw "E2E failed after $($retries + 1) attempts: $($_.Exception.Message)"
      }
    }
  }
}

if (Test-Path ".\e2e\playwright.config.ts") {
  Run-E2E-With-Retry 1
}
