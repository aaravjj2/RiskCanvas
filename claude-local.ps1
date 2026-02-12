param(
  [Parameter(Mandatory=$true)]
  [string]$Prompt
)

$env:ANTHROPIC_AUTH_TOKEN="ollama"
$env:ANTHROPIC_API_KEY=""
$env:ANTHROPIC_BASE_URL="http://localhost:11434"

claude --model qwen3-coder:30b -p $Prompt
