@echo off
setlocal EnableExtensions

set "G_CHECK="
if /i "%~1"=="--check" set "G_CHECK=1"
if "%~1"=="/?" goto :usage
if /i "%~1"=="--help" goto :usage
if not "%~1"=="" if not defined G_CHECK exit /b 2
if not "%~2"=="" exit /b 2

pushd "%~dp0"
if errorlevel 1 exit /b 1
set "G_STEP=activate mkdocs_desk"
call activate mkdocs_desk
if errorlevel 1 goto :failed
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "G_SITE=.peicd100\codex\tmp\g-deploy\site"

if defined G_CHECK goto :build
set "G_STEP=verify main branch"
set "G_BRANCH="
for /f "delims=" %%B in ('call git branch --show-current') do set "G_BRANCH=%%B"
if not "%G_BRANCH%"=="main" (
    echo ERROR: g publishes from main only. No branch was renamed.
    popd
    exit /b 1
)

:build
set "G_STEP=build documentation"
echo [g] Building with mkdocs_desk; preview site is left untouched.
call python -m mkdocs build -f mkdocs.yml -d "%G_SITE%" --clean
if errorlevel 1 goto :failed
if defined G_CHECK (
    echo [g] Check passed. No commit, deployment or push was performed.
    goto :done
)

set "G_STEP=check staged private memory"
call git diff --cached --quiet -- .peicd100/codex .peicd100/codex_compressed .codex codex
if errorlevel 1 (
    echo ERROR: memory files are already staged or Git inspection failed. Review the index manually.
    popd
    exit /b 1
)
set "G_STEP=stage source changes"
call git add --all -- . ":(top,glob,exclude)[.]peicd100/codex/**" ":(top,glob,exclude)[.]peicd100/codex_compressed/**" ":(top,glob,exclude)[.]codex/**" ":(top,glob,exclude)[c]odex/**"
if errorlevel 1 goto :failed
set "G_STEP=inspect staged source changes"
call git diff --cached --quiet
if errorlevel 2 goto :failed
if not errorlevel 1 goto :deploy
set "G_STEP=commit source changes"
call git commit -m "PEICD100"
if errorlevel 1 goto :failed

:deploy
set "G_STEP=deploy validated site"
echo [g] Deploying the validated build; no second full build is needed.
call python "%~dp0tools\publish_built_site.py" --site-dir "%G_SITE%"
if errorlevel 1 goto :failed
set "G_STEP=push main"
call git push -u origin main
if errorlevel 1 goto :failed
echo [g] Deployment and source push completed.

:done
popd
exit /b 0

:failed
set "G_EXIT=%errorlevel%"
if "%G_EXIT%"=="0" set "G_EXIT=1"
echo ERROR: g stopped at "%G_STEP%" ^(exit %G_EXIT%^). Later steps were not run.
popd
exit /b %G_EXIT%

:usage
echo Usage: g [--check]
echo --check builds locally only. Plain g commits source and publishes after a successful build.
exit /b 0
