@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "PREVIEW_ENV=mkdocs_desk"
set "CONDA_ROOT="

if "%~1"=="/?" goto :usage
if /i "%~1"=="--help" goto :usage

cd /d "%ROOT%"

if defined CONDA_BASE if exist "%CONDA_BASE%\condabin\conda.bat" set "CONDA_ROOT=%CONDA_BASE%"
set "CONDA_BASE="

if not defined CONDA_ROOT call :detect_conda_root
if not defined CONDA_ROOT (
    echo Conda base not found. Set CONDA_ROOT or CONDA_BASE first.
    exit /b 1
)

call "%CONDA_ROOT%\condabin\conda.bat" activate %PREVIEW_ENV%
if errorlevel 1 (
    echo Failed to activate env: %PREVIEW_ENV%
    exit /b 1
)

python "%ROOT%tools\update_preview_config.py" %*
if errorlevel 1 exit /b %errorlevel%

if /i "%PREVIEW_SKIP_SERVE%"=="1" (
    echo Prepared preview target. Skipped mkdocs serve because PREVIEW_SKIP_SERVE=1.
    exit /b 0
)

rem Conditional exit prevents Ctrl+C from showing "Terminate batch job (Y/N)".
python -m mkdocs serve -f mkdocs.preview.yml --dirty && exit /b 0 || exit /b 1

:detect_conda_root
for %%D in (
    "C:\ProgramData\Anaconda3"
    "C:\ProgramData\Miniconda3"
    "%USERPROFILE%\anaconda3"
    "%USERPROFILE%\miniconda3"
    "%LOCALAPPDATA%\anaconda3"
    "%LOCALAPPDATA%\miniconda3"
    "%LOCALAPPDATA%\miniforge3"
    "%USERPROFILE%\miniforge3"
) do (
    if exist "%%~D\condabin\conda.bat" (
        set "CONDA_ROOT=%%~D"
        goto :eof
    )
)
goto :eof

:usage
echo Usage: preview.bat [Markdown path]
echo Example: preview.bat docs\md\...\file.md
echo Without a path, preview.bat uses the previous target in mkdocs.preview.yml.
exit /b 1
