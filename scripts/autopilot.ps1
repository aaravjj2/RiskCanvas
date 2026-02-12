param(
  [string]$Model = "qwen3-coder:30b",
  [int]$MaxFixAttempts = 5,
  [int]$MaxTurns = 64
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

function SafeCommitMsg([string]$taskLine) {
  $msg = $taskLine -replace "^- \[ \] ",""
  $msg = $msg -replace '[^\x20-\x7E]', ''   # strip non-ascii to avoid weird glyphs
  if ($msg.Length -gt 72) { $msg = $msg.Substring(0,72) }
  return "Complete: $msg"
}

function ClaudeDo([string]$prompt, [string]$tag) {
  $env:ANTHROPIC_AUTH_TOKEN="ollama"
  $env:ANTHROPIC_API_KEY=""
  $env:ANTHROPIC_BASE_URL="http://localhost:11434"

  $log = "artifacts/logs/$((Get-Date).ToString('yyyyMMdd-HHmmss'))-$tag.log"
  Write-Host "Claude log => $log"

  $args = @(
    "-p",
    "--model", $Model,
    "--max-turns", "$MaxTurns",
    "--dangerously-skip-permissions",
    "--disallowedTools", "Bash(rm *)",
    "--disallowedTools", "Bash(del *)",
    "--disallowedTools", "Bash(rmdir *)",
    "--disallowedTools", "Bash(Remove-Item *)",
    "--",
    $prompt
  )

  $out = (& claude @args 2>&1 | Tee-Object -FilePath $log | Out-String)

  if ($LASTEXITCODE -ne 0) { throw "Claude failed ($LASTEXITCODE). See $log" }
  if ($out -match "Reached max turns") { throw "Claude hit max turns. Increase -MaxTurns or tighten the task. See $log" }
}

# Require origin remote
$remotes = & git remote
if ($LASTEXITCODE -ne 0 -or -not ($remotes -match "origin")) {
  throw "No git remote 'origin' set."
}

while ($true) {
  $task = NextTask
  if ($null -eq $task) { Write-Host "`n✅ No remaining tasks. Exiting."; exit 0 }

  Write-Host "`n=== NEXT TASK ==="
  Write-Host $task.Text

  $impl = @"
You are in C:\dev\repos\myrepo.
Follow CLAUDE.md strictly (determinism + tests + data-testid only).
Implement ONLY this single task line:

$($task.Text)

Rules:
- Minimal changes.
- Add tests as needed.
- Do NOT mark tasks complete.
- After implementing, summarize what changed and why.
"@

  ClaudeDo $impl "implement"

  $ok = $false
  for ($attempt=1; $attempt -le $MaxFixAttempts; $attempt++) {
    try {
      & .\scripts\testgate.ps1
      $ok = $true
      break
    } catch {
      $err = $_.Exception.Message
      Write-Host "`nTestgate failed (attempt $attempt/$MaxFixAttempts): $err"

      $fix = @"
scripts/testgate.ps1 failed. Fix ONLY what is needed to make it pass.
Error:
$err
"@
      ClaudeDo $fix "fix"
    }
  }

  if (-not $ok) { throw "Gates never passed. Stopping to avoid bad commits." }

  MarkDone $task.Index

  git add -A
  if (-not (git status --porcelain)) {
    Write-Host "No changes to commit; continuing."
    continue
  }

  $msg = SafeCommitMsg $task.Text
  git commit -m $msg
  git push

  Write-Host "`n✅ Completed and pushed: $msg"
}
