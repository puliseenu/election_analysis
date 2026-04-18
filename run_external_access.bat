@echo off
REM ========================================
REM ELECTION DASHBOARD - PUBLIC ACCESS
REM This script starts the dashboard with
REM a public ngrok URL for external access
REM ========================================

echo.
echo ========================================================
echo  ELECTION DASHBOARD - EXTERNAL ACCESS (NGROK)
echo ========================================================
echo.

cd /d "%~dp0"

REM Kill any existing Python processes on port 8050
echo [*] Cleaning up old processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

REM Start the external access wrapper
echo [*] Starting dashboard with external URL...
echo.

.venv\Scripts\python.exe external_access_wrapper.py

echo.
echo ========================================================
echo  Dashboard stopped
echo ========================================================
pause
