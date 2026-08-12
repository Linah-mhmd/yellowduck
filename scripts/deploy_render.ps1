# Yellow Duck — Deploy to Render (run in PowerShell)

$ErrorActionPreference = "Stop"
$git = "C:\xampp\htdocs\alrefi\Git\cmd\git.exe"
$gh = "$env:ProgramFiles\GitHub CLI\gh.exe"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

Set-Location $root

Write-Host "=== Step 1: GitHub login ===" -ForegroundColor Cyan
& $gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Browser will open — login to GitHub and approve."
    & $gh auth login -w -p https -h github.com
}

Write-Host "`n=== Step 2: Create GitHub repo & push ===" -ForegroundColor Cyan
$visibility = Read-Host "Repo visibility: private or public (default: private)"
if (-not $visibility) { $visibility = "private" }
$repoName = Read-Host "Repo name on GitHub (e.g. yellowduck)"
if (-not $repoName) { $repoName = "yellowduck" }

$visFlag = if ($visibility -eq "public") { "--public" } else { "--private" }
& $gh repo create $repoName $visFlag --source=. --remote=origin --push
if ($LASTEXITCODE -ne 0) {
    Write-Host "If repo exists, try: git remote add origin https://github.com/YOUR_USER/$repoName.git"
    Write-Host "Then: git push -u origin main"
    & $git branch -M main
    & $git push -u origin main
}

Write-Host "`n=== Step 3: Open Render ===" -ForegroundColor Cyan
Write-Host "1. Go to https://dashboard.render.com"
Write-Host "2. Sign in with GitHub"
Write-Host "3. New + -> Web Service -> select repo '$repoName'"
Write-Host "4. Runtime: Docker | Plan: Free"
Write-Host "5. Paste env vars from render-env-copypaste.txt"
Write-Host "6. After deploy, update CORS_ORIGINS + FRONTEND_URL with your Render URL"
Write-Host ""
Start-Process "https://dashboard.render.com/select-repo?type=web"

Write-Host "Done. Repo pushed — finish Render setup in the browser." -ForegroundColor Green
