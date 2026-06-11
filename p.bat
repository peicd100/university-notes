@echo off
setlocal EnableExtensions

call "%~dp0preview.bat" %*
exit /b %errorlevel%
