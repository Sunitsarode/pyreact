@echo off
echo ========================================
echo Starting Live Analyser
echo ========================================
echo.

echo [1/2] Starting Backend Server...
start "Backend Server" cmd /k "cd backend && python app.py"
timeout /t 3

echo [2/2] Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Both servers are starting...
echo Backend:  http://localhost:5001
echo Frontend: http://localhost:3000
echo ========================================
echo.
echo Press any key to stop all servers...
pause

echo Stopping servers...
taskkill /FI "WINDOWTITLE eq Backend Server*" /F
taskkill /FI "WINDOWTITLE eq Frontend Server*" /F
