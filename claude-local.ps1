param(
  [Parameter(Mandatory=$true)]
  [string]$Prompt
)

$env:ANTHROPIC_AUTH_TOKEN="ollama"
$env:ANTHROPIC_API_KEY=""
$env:ANTHROPIC_BASE_URL="http://localhost:11434"

# Print mode with explicit end-of-options separator
claude -p --model qwen3-coder:30b -- $Prompt
