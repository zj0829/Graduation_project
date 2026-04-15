@echo off
chcp 65001 >nul
title Pentest System - Starter
color 0A

echo ============================================================
echo   LLM-based Web Pentest Intelligent Assistant
echo   One-click Start Script
echo ============================================================
echo.

set DOCKER="C:\Program Files\Docker\Docker\resources\bin\docker.exe"

echo [1/4] Checking Docker Desktop...
%DOCKER% info >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Docker Desktop is not running. Please start it first.
    pause
    exit /b 1
)
echo   [OK] Docker Desktop is running

echo.
echo [2/4] Starting security tool containers...
%DOCKER% network create pentest-network >nul 2>&1

%DOCKER% ps -a --format "{{.Names}}" | findstr /C:"pentest-nmap" >nul 2>&1
if %errorlevel% neq 0 (
    echo   - Starting Nmap container...
    %DOCKER% run -d --name pentest-nmap --network pentest-network --entrypoint="" instrumentisto/nmap:latest sleep infinity >nul 2>&1
) else (
    %DOCKER% start pentest-nmap >nul 2>&1
    echo   - Nmap container started
)

%DOCKER% ps -a --format "{{.Names}}" | findstr /C:"pentest-amass" >nul 2>&1
if %errorlevel% neq 0 (
    echo   - Starting Amass container...
    %DOCKER% run -d --name pentest-amass --network pentest-network --entrypoint="" caffix/amass:latest sleep infinity >nul 2>&1
) else (
    %DOCKER% start pentest-amass >nul 2>&1
    echo   - Amass container started
)

%DOCKER% ps -a --format "{{.Names}}" | findstr /C:"pentest-sqlmap" >nul 2>&1
if %errorlevel% neq 0 (
    echo   - Starting SQLmap container...
    %DOCKER% run -d --name pentest-sqlmap --network pentest-network --entrypoint="" pentest-sqlmap:latest sleep infinity >nul 2>&1
) else (
    %DOCKER% start pentest-sqlmap >nul 2>&1
    echo   - SQLmap container started
)

%DOCKER% ps -a --format "{{.Names}}" | findstr /C:"pentest-owasp-zap" >nul 2>&1
if %errorlevel% neq 0 (
    echo   - Starting OWASP ZAP container...
    %DOCKER% run -d --name pentest-owasp-zap --network pentest-network -p 8090:8090 -e TZ=Asia/Shanghai zaproxy/zap-stable:latest zap.sh -daemon -port 8090 -host 0.0.0.0 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true -config api.key= >nul 2>&1
) else (
    %DOCKER% start pentest-owasp-zap >nul 2>&1
    echo   - OWASP ZAP container started
)

%DOCKER% ps -a --format "{{.Names}}" | findstr /C:"pentest-metasploit-db" >nul 2>&1
if %errorlevel% neq 0 (
    echo   - Starting Metasploit DB container...
    %DOCKER% run -d --name pentest-metasploit-db --network pentest-network -e POSTGRES_USER=msf -e POSTGRES_PASSWORD=msf_2026_secure -e POSTGRES_DB=msf postgres:15-alpine >nul 2>&1
) else (
    %DOCKER% start pentest-metasploit-db >nul 2>&1
    echo   - Metasploit DB container started
)

%DOCKER% ps -a --format "{{.Names}}" | findstr /C:"pentest-metasploit" | findstr /V "db" >nul 2>&1
if %errorlevel% neq 0 (
    echo   - Starting Metasploit container...
    %DOCKER% run -d --name pentest-metasploit --network pentest-network -p 55553:55553 -p 4444:4444 -e MSF_DATABASE_CONFIG=postgres://msf:msf_2026_secure@pentest-metasploit-db:5432/msf --entrypoint="" metasploitframework/metasploit-framework:latest sleep infinity >nul 2>&1
) else (
    %DOCKER% start pentest-metasploit >nul 2>&1
    echo   - Metasploit container started
)

echo   [OK] All containers started

echo.
echo [3/4] Starting MCP service (port 9876)...
powershell -WindowStyle Hidden -Command "Start-Process cmd -ArgumentList '/c chcp 65001 >nul && cd /d %~dp0mcp-server && node server.js' -WindowStyle Hidden"
timeout /t 3 /nobreak >nul
echo   [OK] MCP service started

echo.
echo [4/4] Starting backend API service (port 8000)...
powershell -WindowStyle Hidden -Command "Start-Process cmd -ArgumentList '/c chcp 65001 >nul && cd /d %~dp0 && python main.py' -WindowStyle Hidden"
timeout /t 4 /nobreak >nul
echo   [OK] Backend service started

echo.
echo ============================================================
echo   System started successfully!
echo.
echo   Frontend:  http://localhost:8000/static/index.html
echo   API Docs:  http://localhost:8000/docs
echo   MCP:       http://localhost:9876/health
echo.
echo   Test Target: testphp.vulnweb.com (OWASP legal range)
echo ============================================================
echo.
echo Press any key to open browser...
pause >nul
start http://localhost:8000/static/index.html
