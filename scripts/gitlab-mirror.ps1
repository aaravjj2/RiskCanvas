<#
.SYNOPSIS
    Mirror a GitHub repo to GitLab.

.DESCRIPTION
    Sets up a dual-remote Git configuration so that pushes go to both
    GitHub (origin) and GitLab (gitlab). Designed for CI-driven mirroring.

.PARAMETER GitLabUrl
    The GitLab remote URL (HTTPS or SSH).

.EXAMPLE
    .\gitlab-mirror.ps1 -GitLabUrl "https://gitlab.com/org/riskcanvas.git"
#>

param(
    [Parameter(Mandatory)]
    [string]$GitLabUrl
)

$ErrorActionPreference = "Stop"

# Check if gitlab remote already exists
$remotes = git remote
if ($remotes -contains "gitlab") {
    Write-Host "Remote 'gitlab' already exists. Updating URL..."
    git remote set-url gitlab $GitLabUrl
} else {
    Write-Host "Adding remote 'gitlab'..."
    git remote add gitlab $GitLabUrl
}

Write-Host "Fetching from origin..."
git fetch origin

Write-Host "Pushing all branches to gitlab..."
git push gitlab --all --force

Write-Host "Pushing all tags to gitlab..."
git push gitlab --tags --force

Write-Host "Mirror complete."
