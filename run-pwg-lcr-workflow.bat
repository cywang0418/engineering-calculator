@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "CASE_DIR=%PROJECT_ROOT%qspice-cli-validation\examples\pwg-lcr"
set "REPORTS_DIR=%PROJECT_ROOT%reports"
set "CSV_FILE=%CASE_DIR%\pwg_lcr.csv"

pushd "%PROJECT_ROOT%"
if exist "%CSV_FILE%" (
  python -m src.qspice_tools.pwg_lcr_workflow --case-dir "%CASE_DIR%" --reports-dir "%REPORTS_DIR%" --csv "%CSV_FILE%" %*
) else (
  python -m src.qspice_tools.pwg_lcr_workflow --case-dir "%CASE_DIR%" --reports-dir "%REPORTS_DIR%" %*
)
set "RESULT=%ERRORLEVEL%"
popd

exit /b %RESULT%
