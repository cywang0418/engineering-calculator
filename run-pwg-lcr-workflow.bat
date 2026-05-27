@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "CASE_DIR=%PROJECT_ROOT%qspice-cli-validation\examples\pwg-lcr"
set "REPORTS_DIR=%PROJECT_ROOT%reports"
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
"%PYTHON_CMD%" -m src.qspice_tools.pwg_lcr_workflow --case-dir "%CASE_DIR%" --reports-dir "%REPORTS_DIR%" %*
set "RESULT=%ERRORLEVEL%"
popd

exit /b %RESULT%
