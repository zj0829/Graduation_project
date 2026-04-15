@echo off
chcp 65001 >nul
title Pentest System - Stopper
color 0C

echo ============================================================
echo   Stopping All Services
echo ============================================================
echo.

echo [1/2] Stopping backend and MCP services...
taskkill /FI "WINDOWTITLE eq Backend-API*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq MCP-Server*" /F >nul 2>&1
powershell -Command "Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -eq '' -and $_.CommandLine -match 'uvicorn'} | Stop-Process -Force" >nul 2>&1
powershell -Command "Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'server.js'} | Stop-Process -Force" >nul 2>&1
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
echo   [OK] Processes stopped

echo.
echo [2/2] Stopping Docker containers...
set DOCKER="C:\Program Files\Docker\Docker\resources\bin\docker.exe"
%DOCKER% stop pentest-nmap pentest-amass pentest-sqlmap pentest-owasp-zap pentest-metasploit pentest-metasploit-db >nul 2>&1
echo   [OK] Containers stopped

echo.
echo ============================================================
echo   All services stopped
echo ============================================================
pause
