param(
  [string]$Model = "qwen3-coder:30b",
  [int]$MaxFixAttempts = 5,
  [int]$MaxTurns = 64,

  # run-control
  [int]$RunForHours = 168,           # 7 days
  [int]$IdleSleepSeconds = 300,      # when no tasks
  [switch]$Watch = $true,            # keep running when TASKS is empty
  [switch]$ContinueOnFailure = $true # don't die on one task; mark blocked and move on
)

$ErrorActionPreference = "Stop"

# Always run from repo root (script is in /scripts)
Set-Location (Resolve-Path "$PSScriptRoot\..")

# Ensure log dir exists
New-Item -ItemType Directory -Force -Path ".\artifacts\logs" | Out-Null

$deadline = (Get-Date).AddHours($RunForHours)

function NextTask {
  $lines = Get-Content ".\TASKS.md"
  for ($i=0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    if ($line -match "^- \[ \] " -and $line -notmatch "\[blocked\]") {
      return @{ Index = $i; Text = $line }
    }
  }
  return $null
}

function MarkDone([int]$Index) {
  $lines = Get-Content ".\TASKS.md"
  $lines[$Index] = $lines[$Index] -replace "^- \[ \] ","- [x] "
  Set-Content -Encoding UTF8 ".\TASKS.md" $lines
}

function MarkBlocked([int]$Index, [string]$Reason) {
  $lines = Get-Content ".\TASKS.md"
  $clean = $Reason -replace "[\r\n]+"," "  # one line
  if ($clean.Length -gt 140) { $clean = $clean.Substring(0,140) }

  # keep it unchecked but tag it so NextTask skips it
  $lines[$Index] = $lines[$Index] -replace "^- \[ \] ","- [ ] [blocked] "
  $lines[$Index] = "$($lines[$Index])  // $clean"
  Set-Content -Encoding UTF8 ".\TASKS.md" $lines
}

function SafeCommitMsg([string]$taskLine) {
  $msg = $taskLine -replace "^- \[ \] ",""
  $msg = $msg -replace '[^\x20-\x7E]', ''
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
  if ($out -match "Reached max turns") { throw "Claude hit max turns. See $log" }
}

# Require origin remote
$remotes = & git remote
if ($LASTEXITCODE -ne 0 -or -not ($remotes -match "origin")) {
  throw "No git remote 'origin' set."
}

while ($true) {
  if ((Get-Date) -gt $deadline) {
    Write-Host "`n⏱️ RunForHours reached. Exiting."
    exit 0
  }

  $task = NextTask
  if ($null -eq $task) {
    if ($Watch) {
      Write-Host "`n🟡 No remaining tasks. Sleeping $IdleSleepSeconds sec (watch mode)."
      Start-Sleep -Seconds $IdleSleepSeconds
      continue
    } else {
      Write-Host "`n✅ No remaining tasks. Exiting."
      exit 0
    }
  }

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

  try {
    ClaudeDo $impl "implement"
  } catch {
    $err = $_.Exception.Message
    Write-Host "`nImplement failed: $err"
    if ($ContinueOnFailure) {
      MarkBlocked $task.Index $err
      git add TASKS.md
      git commit -m "chore: block task (autopilot)" | Out-Null
      git push | Out-Null
      continue
    }
    throw
  }

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
      try {
        ClaudeDo $fix "fix"
      } catch {
        $fixErr = $_.Exception.Message
        Write-Host "`nFix step failed: $fixErr"
        break
      }
    }
  }

  if (-not $ok) {
    $msg = "Gates never passed after $MaxFixAttempts attempts."
    Write-Host "`n$msg"
    if ($ContinueOnFailure) {
      MarkBlocked $task.Index $msg
      git add TASKS.md
      git commit -m "chore: block task (autopilot)" | Out-Null
      git push | Out-Null
      continue
    }
    throw "Gates never passed. Stopping to avoid bad commits."
  }

  # Stage changes FIRST; if nothing changed, do NOT mark task done.
  git add -A
  $porcelain = git status --porcelain
  if (-not $porcelain) {
    Write-Host "No changes to commit; leaving task unchecked."
    continue
  }

  # Now mark done and include it in same commit
  MarkDone $task.Index
  git add TASKS.md

  $msg = SafeCommitMsg $task.Text
  git commit -m $msg
  git push

  Write-Host "`n✅ Completed and pushed: $msg"
}