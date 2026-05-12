@echo off
setlocal

set "QSPICE_EXE=C:\Program Files\QSPICE\QSPICE64.exe"
set "CASE_DIR=%~dp0..\examples\rc-lowpass"
set "CIR_FILE=%CASE_DIR%\rc_lowpass.cir"

echo QSPICE executable:
echo   %QSPICE_EXE%
echo.
echo Circuit file:
echo   %CIR_FILE%
echo.

if not exist "%QSPICE_EXE%" (
  echo ERROR: QSPICE executable not found.
  echo Please edit QSPICE_EXE in this batch file.
  exit /b 1
)

if not exist "%CIR_FILE%" (
  echo ERROR: Circuit file not found.
  exit /b 1
)

pushd "%CASE_DIR%"
"%QSPICE_EXE%" "rc_lowpass.cir"
set "RESULT=%ERRORLEVEL%"
popd

echo.
echo QSPICE exit code: %RESULT%
echo.

if exist "%CASE_DIR%\rc_lowpass.qraw" (
  echo Found rc_lowpass.qraw
) else (
  echo Missing rc_lowpass.qraw
)

if exist "%CASE_DIR%\rc_lowpass.log" (
  echo Found rc_lowpass.log
) else (
  echo Missing rc_lowpass.log
)

exit /b %RESULT%
