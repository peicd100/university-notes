@echo off
setlocal EnableExtensions
call "%~dp0tools\activate_mkdocs.bat"
if errorlevel 1 exit /b %errorlevel%
pushd "%~dp0"
if errorlevel 1 exit /b 1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
python -m tools.serve_site %*
set "S_EXIT=%errorlevel%"
popd
exit /b %S_EXIT%
