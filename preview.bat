@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"

if "%~1"=="/?" goto :usage
if /i "%~1"=="--help" goto :usage

cd /d "%ROOT%"

if not defined PREVIEW_CONDA_READY (
    call "%~dp0tools\activate_mkdocs.bat"
    if errorlevel 1 exit /b 1
)

python "%ROOT%tools\update_preview_config.py" %*
if errorlevel 1 exit /b %errorlevel%

if /i "%PREVIEW_SKIP_SERVE%"=="1" (
    echo Prepared preview target. Skipped mkdocs serve because PREVIEW_SKIP_SERVE=1.
    exit /b 0
)

python -m mkdocs serve -f mkdocs.preview.yml --dirty
exit /b %errorlevel%

:usage
echo Usage: preview.bat [Markdown path]
echo Example: preview.bat docs\md\...\file.md
echo Without a path, preview.bat uses the previous target in mkdocs.preview.yml.
exit /b 1
