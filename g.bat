@echo off
setlocal EnableExtensions

pushd "%~dp0"

call activate mkdocs_desk
mkdocs gh-deploy
git add .
git commit -m "PEICD100"
git branch -M main
git push -u origin main

set "exit_code=%errorlevel%"
popd
exit /b %exit_code%
