@echo off
setlocal
set "REPO_ROOT=%~dp0.."
pushd "%REPO_ROOT%" >nul 2>&1
if errorlevel 1 (
    echo LUXIOM local development repository is unavailable.
    exit /b 1
)

set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo LUXIOM local development virtual environment is unavailable.
    popd
    exit /b 1
)

"%PYTHON_EXE%" "%REPO_ROOT%\scripts\launch_local_interactive.py"
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
