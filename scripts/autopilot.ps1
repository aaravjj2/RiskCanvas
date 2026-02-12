param(
  [string]$Model = "qwen3-coder:30b",
  [int]$MaxFixAttempts = 3
)

$ErrorActionPreference = "Stop"

function NextTask {
  $lines = Get-Content ".\TASKS.md"
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "^- \[ \] ") { return @{Index=$i; Text=$lines[$i]} }
  }
  return $null
}

function MarkDone([int]$Index) {
  $lines = Get-Content ".\TASKS.md"
  $lines[$Index] = $lines[$Index] -replace "^- \[ \] ","- [x] "
  Set-Content -Encoding UTF8 ".\TASKS.md" $lines
}

function ClaudeDo([string]$prompt, [string]$tag) {
  $env:ANTHROPIC_AUTH_TOKEN="ollama"
  $env:ANTHROPIC_API_KEY=""
  $env:ANTHROPIC_BASE_URL="http://localhost:11434"

  $log = "artifacts/logs/$((Get-Date).ToString('yyyyMMdd-HHmmss'))-$tag.log"
  Write-Host "Claude log => $log"

  # IMPORTANT: Do not pipe stdin into claude on Windows (Ink raw-mode issues).
  # Use print mode (-p/--print) with the prompt as an argument. :contentReference[oaicite:2]{index=2}
  $args = @(
    "-p",
    "--model", $Model,
    "--max-turns", "14",
    "--dangerously-skip-permissions",
    "--disallowedTools", "Bash(rm *)",
    "--disallowedTools", "Bash(del *)",
    "--disallowedTools", "Bash(rmdir *)",
    "--disallowedTools", "Bash(Remove-Item *)",
    "--",
    $prompt
  )

  & claude @args 2>&1 | Tee-Object -FilePath $log

  if ($LASTEXITCODE -ne 0) {
    throw "Claude run failed ($LASTEXITCODE). See $log"
  }
}

# Sanity: require git remote
$remotes = & git remote
if ($LASTEXITCODE -ne 0 -or -not ($remotes -match "origin")) {
  throw "No git remote 'origin' set. Set it once: git remote add origin YOUR_URL"
}

while ($true) {
  $task = NextTask
  if ($null -eq $task) {
    Write-Host "`n✅ No remaining tasks. Exiting."
    exit 0
  }

  Write-Host "`n=== NEXT TASK ==="
  Write-Host $task.Text

  $impl = @"
You are in C:\dev\repos\myrepo.
Follow CLAUDE.md strictly (determinism + tests + data-testid-only).
Implement ONLY this single task line:

$($task.Text)

Rules:
- Minimal changes.
- Add tests as needed.
- Do NOT mark tasks complete yourself.
- After implementing, summarize what changed and why.
"@

  ClaudeDo $impl "implement"

  $attempt = 0
  while ($true) {
    try {
      & powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\testgate.ps1
      break
    } catch {
      $attempt++
      if ($attempt -gt $MaxFixAttempts) { throw "Testgate failed too many times. Stopping." }

      $fix = @"
scripts/testgate.ps1 failed. Fix ONLY what is needed to make it pass.
Error:
$($_.Exception.Message)
"@
      ClaudeDo $fix "fix"
    }
  }

  MarkDone $task.Index

  git add -A
  git commit -m ("Complete: " + $task.Text)
  git push

  Write-Host "`n✅ Completed and pushed: $($task.Text)"
}


