@echo off
rem Called inside each launcher's SETLOCAL so activation stays local.
if not defined CONDA_BAT set "CONDA_BAT=C:\ProgramData\anaconda3\condabin\conda.bat"
if not exist "%CONDA_BAT%" (
    echo ERROR: Conda was not found at "%CONDA_BAT%".
    exit /b 1
)
call "%CONDA_BAT%" activate "D:\conda\envs\mkdocs_desk"
exit /b %errorlevel%
