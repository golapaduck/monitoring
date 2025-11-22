@echo off
chcp 65001 >nul
echo ========================================
echo   Monitoring System Starting
echo ========================================
echo.

echo [1/2] Starting Backend Server...
start "Backend (Flask)" cmd /k "chcp 65001 >nul && cd backend && python -u app.py"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Frontend Server...
start "Frontend (React)" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   Servers Started!
echo   - Backend:  http://localhost:25575
echo   - Frontend: http://localhost:5173
echo ========================================
echo.
