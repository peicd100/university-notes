@echo off
setlocal EnableExtensions

rem Legacy fallback. Typing "p" should resolve to p.exe before this file.
rem Explicitly running p.bat may still be subject to cmd's batch Ctrl+C prompt.
"%~dp0preview.bat" %*
