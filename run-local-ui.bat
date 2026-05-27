@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "PYTHON_CMD=%PYTHON%"

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
echo Opening QSPICE Engineering Calculator UI at http://127.0.0.1:8765
start "" http://127.0.0.1:8765
"%PYTHON_CMD%" -m src.qspice_tools.local_app 8765
set "RESULT=%ERRORLEVEL%"
popd

exit /b %RESULT%
