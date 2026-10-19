@echo off
setlocal EnableExtensions
set "S_ENV=D:\conda\envs\mkdocs_desk"
if defined CONDA_PREFIX if /i "%CONDA_DEFAULT_ENV%"=="mkdocs_desk" set "S_ENV=%CONDA_PREFIX%"
if not exist "%S_ENV%\python.exe" (
    echo ERROR: mkdocs_desk Python was not found. Activate mkdocs_desk and try again.
    exit /b 1
)
pushd "%~dp0"
if errorlevel 1 exit /b 1
set "PATH=%S_ENV%;%S_ENV%\Scripts;%S_ENV%\Library\bin;%PATH%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
"%S_ENV%\python.exe" -m tools.serve_site %*
set "S_EXIT=%errorlevel%"
popd
exit /b %S_EXIT%
