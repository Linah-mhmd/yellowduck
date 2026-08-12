# Yellow Duck — Deploy to Koyeb (run after: koyeb login OR pass -Token)
param(
    [Parameter(Mandatory = $true)]
    [string]$Token
)

$ErrorActionPreference = "Stop"
$koyeb = "$env:USERPROFILE\.koyeb\bin\koyeb.exe"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

if (-not (Test-Path $koyeb)) {
    Write-Error "Koyeb CLI not found. Run from project after CLI install."
}

Set-Location $root

# Load secrets from local .env (not committed)
$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) {
    Write-Error ".env not found"
}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        Set-Variable -Name "env_$($matches[1].Trim())" -Value $matches[2].Trim() -Scope Script
    }
}

$mongoUri = $env_MONGO_URI
$secretKey = if ($env_SECRET_KEY -and $env_SECRET_KEY -notmatch 'change-this') { $env_SECRET_KEY } else { '8744361735258ba208b9230e20c3ac82dec9321beb9b62d0bde0fa2b3f349240' }

# Initial CORS — updated after deploy if URL differs
$cors = "https://yellowduck.koyeb.app"
$frontend = "https://yellowduck.koyeb.app"

Write-Host "=== Deploying yellowduck to Koyeb ===" -ForegroundColor Cyan

& $koyeb apps init yellowduck `
    --token $Token `
    --git "github.com/Linah-mhmd/yellowduck" `
    --git-branch main `
    --git-builder docker `
    --instance-type nano `
    --regions fra `
    --ports "8000:http" `
    --routes "/:8000" `
    --env "PORT=8000" `
    --env "MONGO_URI=$mongoUri" `
    --env "MONGO_DB=graduation" `
    --env "SECRET_KEY=$secretKey" `
    --env "FLASK_DEBUG=false" `
    --env "SESSION_COOKIE_SECURE=true" `
    --env "SESSION_COOKIE_SAMESITE=Lax" `
    --env "REQUIRE_EMAIL_VERIFICATION=false" `
    --env "SMTP_ENABLED=false" `
    --env "CORS_ORIGINS=$cors" `
    --env "FRONTEND_URL=$frontend"

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Check: https://app.koyeb.com"
Write-Host "After deploy, update CORS_ORIGINS + FRONTEND_URL if URL differs from $cors"
