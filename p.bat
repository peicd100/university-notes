@echo off
setlocal EnableExtensions

call "%~dp0tools\activate_mkdocs.bat"
if errorlevel 1 exit /b %errorlevel%
set "PREVIEW_CONDA_READY=1"
call "%~dp0preview.bat" %*
exit /b %errorlevel%
