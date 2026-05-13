@echo off
setlocal

set "DEFAULT_QSPICE_EXE=C:\Program Files\QSPICE\QSPICE64.exe"

if "%~1"=="" (
  echo Usage: scripts\run-qspice-circuit.bat path\to\circuit.cir
  exit /b 2
)

set "CIR_FILE=%~f1"
set "CASE_DIR=%~dp1"
set "CASE_NAME=%~n1"

if "%QSPICE_EXE%"=="" (
  set "QSPICE_EXE=%DEFAULT_QSPICE_EXE%"
)

echo QSPICE executable:
echo   %QSPICE_EXE%
echo.
echo Circuit file:
echo   %CIR_FILE%
echo.

if not exist "%QSPICE_EXE%" (
  echo ERROR: QSPICE executable not found.
  echo Set QSPICE_EXE or edit this script.
  exit /b 1
)

if not exist "%CIR_FILE%" (
  echo ERROR: Circuit file not found.
  exit /b 1
)

pushd "%CASE_DIR%"
"%QSPICE_EXE%" "%CIR_FILE%"
set "RESULT=%ERRORLEVEL%"
popd

echo.
echo QSPICE exit code: %RESULT%

if exist "%CASE_DIR%%CASE_NAME%.qraw" (
  echo Found %CASE_NAME%.qraw
) else (
  echo Missing %CASE_NAME%.qraw
)

if exist "%CASE_DIR%%CASE_NAME%.log" (
  echo Found %CASE_NAME%.log
) else (
  echo Missing %CASE_NAME%.log
)

exit /b %RESULT%
