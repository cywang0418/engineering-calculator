@echo off
setlocal

set "CASE_DIR=%~dp0..\examples\rc-lowpass"
call "%~dp0run-qspice-circuit.bat" "%CASE_DIR%\rc_lowpass.cir"
exit /b %ERRORLEVEL%
