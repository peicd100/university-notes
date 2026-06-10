@echo off
setlocal EnableExtensions

rem Conditional exit prevents Ctrl+C from showing "Terminate batch job (Y/N)".
call "%~dp0preview.bat" %* && exit /b 0 || exit /b 1
