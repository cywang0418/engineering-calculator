@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "PYTHON_CMD=%PYTHON%"
set "HOST=127.0.0.1"
set "PORT=8765"
set "CLOUDFLARED=%PROJECT_ROOT%tools\cloudflared.exe"

if not "%~1"=="" set "PORT=%~1"

if not defined QSPICE_UI_USER set "QSPICE_UI_USER=qgen"
if not defined QSPICE_UI_PASSWORD (
  echo Enter a password for the public QSPICE UI.
  echo Remote users will need this password before they can run simulations.
  set /p "QSPICE_UI_PASSWORD=Password: "
)

if not defined QSPICE_UI_PASSWORD (
  echo Password is required for public tunnel mode.
  exit /b 2
)

if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py"
)

if not defined PYTHON_CMD (
  echo Python was not found. Install Python, add it to PATH, or run:
  echo set "PYTHON=C:\Path\To\python.exe"
  exit /b 9009
)

if not exist "%CLOUDFLARED%" (
  where cloudflared >nul 2>nul
  if not errorlevel 1 set "CLOUDFLARED=cloudflared"
)

if not exist "%CLOUDFLARED%" if not "%CLOUDFLARED%"=="cloudflared" (
  echo cloudflared was not found.
  echo Run this once:
  echo powershell -ExecutionPolicy Bypass -File scripts\install-cloudflared.ps1
  exit /b 1
)

pushd "%PROJECT_ROOT%"
echo Starting password-protected local UI on http://%HOST%:%PORT%
start "QGEN Local UI" /min "%PYTHON_CMD%" -m src.qspice_tools.local_app "%HOST%" "%PORT%"
timeout /t 2 /nobreak >nul

echo.
echo Public tunnel is starting. Copy the https://*.trycloudflare.com URL.
echo Username: %QSPICE_UI_USER%
echo Password: the password you entered in this window.
echo.
"%CLOUDFLARED%" tunnel --url "http://%HOST%:%PORT%"
set "RESULT=%ERRORLEVEL%"
popd

exit /b %RESULT%
