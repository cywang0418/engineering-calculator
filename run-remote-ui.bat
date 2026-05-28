@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "PYTHON_CMD=%PYTHON%"
set "HOST=0.0.0.0"
set "PORT=8765"

if not "%~1"=="" set "PORT=%~1"

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

pushd "%PROJECT_ROOT%"
echo QSPICE Engineering Calculator remote UI is listening on http://%HOST%:%PORT%
echo Use this only on a trusted network. Remote users can trigger local QSPICE runs.
"%PYTHON_CMD%" -m src.qspice_tools.local_app "%HOST%" "%PORT%"
set "RESULT=%ERRORLEVEL%"
popd

exit /b %RESULT%
