@echo off
setlocal

set "PORT=8765"
if not "%~1"=="" set "PORT=%~1"

echo Stopping Cloudflare tunnel processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"

echo Stopping local UI listeners on port %PORT%...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$listeners = netstat -ano | Select-String ':%PORT%' | ForEach-Object { ($_ -split '\s+')[-1] } | Sort-Object -Unique; foreach ($pidValue in $listeners) { if ($pidValue -match '^\d+$' -and $pidValue -ne '0') { Stop-Process -Id ([int]$pidValue) -Force -ErrorAction SilentlyContinue } }"

echo Public tunnel stopped.
