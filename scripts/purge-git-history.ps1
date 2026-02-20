param(
    [Parameter(Mandatory = $false)]
    [string]$RepositoryRoot = "."
)

$ErrorActionPreference = "Stop"

Set-Location $RepositoryRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required."
}

if (-not (Get-Command git-filter-repo -ErrorAction SilentlyContinue)) {
    throw "git-filter-repo is required. Install it before running this script."
}

Write-Host "Running git-filter-repo secret purge..."

# Replace known sensitive patterns/files from history.
git filter-repo `
  --force `
  --path env.template `
  --path-glob "*.env" `
  --path-glob "*.pem" `
  --path-glob "*.key" `
  --invert-paths

Write-Host "History rewrite complete."
Write-Host "Next steps:"
Write-Host "1) Rotate all impacted secrets (already required)."
Write-Host "2) Force push: git push --force --all && git push --force --tags"
Write-Host "3) Ask contributors to re-clone."
