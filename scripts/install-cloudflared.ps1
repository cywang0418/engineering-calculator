$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsDir = Join-Path $projectRoot "tools"
$target = Join-Path $toolsDir "cloudflared.exe"
$url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

Write-Host "Downloading cloudflared to $target"
Invoke-WebRequest -Uri $url -OutFile $target

Write-Host "Installed cloudflared:"
& $target --version
