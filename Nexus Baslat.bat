@echo off
setlocal
title Nexus AI Command Center
cd /d "%~dp0"

echo ========================================================
echo   Nexus - Local AI Command Center
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating a virtual environment...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.13 -m venv .venv
        if errorlevel 1 py -3.12 -m venv .venv
        if errorlevel 1 py -3.11 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 goto :error
) else (
    echo [1/3] Virtual environment is ready.
)

echo [2/3] Checking dependencies...
".venv\Scripts\python.exe" scripts\ensure_dependencies.py
if errorlevel 1 goto :error

echo [3/3] Starting Nexus...
echo Make sure your configured AI provider is running.
echo.
".venv\Scripts\python.exe" run_nexus.py
if errorlevel 1 goto :error
goto :eof

:error
echo.
echo Nexus could not start. Review the error above.
pause
exit /b 1
