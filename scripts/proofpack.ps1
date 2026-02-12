param([Parameter(Mandatory=$true)][string]$Milestone)

$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$root = "artifacts/proof/$ts-$Milestone"

New-Item -ItemType Directory -Force -Path $root | Out-Null

$manifest = @()
$manifest += "# MANIFEST"
$manifest += ""
$manifest += "Milestone: $Milestone"
$manifest += "Timestamp: $ts"
$manifest += ""
$manifest += "## Commands run"
$manifest += "- scripts/testgate.ps1"
$manifest += ""
$manifest += "## Inventory"

$copyList = @(
  "e2e/playwright-report",
  "e2e/test-results"
)

foreach ($p in $copyList) {
  if (Test-Path $p) {
    $dest = Join-Path $root ($p -replace "[:\\]", "_")
    Copy-Item -Recurse -Force $p $dest
    $manifest += "- $p -> $dest"
  }
}

$manifest -join "`r`n" | Set-Content -Encoding UTF8 (Join-Path $root "MANIFEST.md")
Write-Host "Proof pack written to $root"
