@echo off
chcp 65001 > nul

:: 매개변수 확인 (full = 백엔드+프론트엔드, 없으면 백엔드만)
set MODE=%1
if "%MODE%"=="" set MODE=backend

echo ========================================
echo   Monitoring 프로젝트 (개발 모드)
echo ========================================
echo.

:: .env 파일에서 PRODUCTION=True를 PRODUCTION=False로 변경
echo [설정] 개발 모드 활성화 중...
if exist ".env" (
    powershell -Command "(Get-Content .env) -replace 'PRODUCTION=True', 'PRODUCTION=False' | Set-Content .env"
)
echo ✅ 개발 모드 활성화
echo.

:: 모드에 따라 실행
if /i "%MODE%"=="full" goto FULL_MODE
if /i "%MODE%"=="backend" goto BACKEND_MODE

:BACKEND_MODE
echo ========================================
echo   백엔드만 실행합니다
echo ========================================
echo.
echo 🔧 백엔드 서버: http://localhost:8080
echo.
echo 프론트엔드는 별도 터미널에서 실행:
echo   cd frontend
echo   npm run dev
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요
echo ========================================
echo.

cd backend
python -u app.py
goto END

:FULL_MODE
echo ========================================
echo   백엔드 + 프론트엔드 통합 실행
echo ========================================
echo.
echo 🔧 백엔드 서버: http://localhost:8080
echo 🎨 프론트엔드 서버: http://localhost:5173
echo.
echo 두 개의 터미널 창이 열립니다:
echo   1. Backend (Flask)
echo   2. Frontend (Vite)
echo.
echo 서버를 중지하려면 각 터미널에서 Ctrl+C를 누르세요
echo ========================================
echo.

:: 백엔드 서버 시작
echo [1/2] 백엔드 서버 시작 중...
start "Monitoring - Backend (Flask)" cmd /k "chcp 65001 > nul && cd backend && python -u app.py"

:: 프론트엔드 서버 시작 전 대기
timeout /t 2 /nobreak > nul

:: 프론트엔드 서버 시작
echo [2/2] 프론트엔드 서버 시작 중...
start "Monitoring - Frontend (Vite)" cmd /k "chcp 65001 > nul && cd frontend && npm run dev"

echo.
echo ✅ 서버 시작 완료!
echo.
pause
goto END

:END
