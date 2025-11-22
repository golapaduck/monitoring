@echo off
REM ============================================
REM 개발 모드 실행 스크립트
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Monitoring System - Development Mode
echo ========================================
echo.

REM 프로젝트 루트 디렉토리로 이동
cd /d "%~dp0.."

REM 환경 변수 설정
set PRODUCTION=False
set FLASK_ENV=development
set FLASK_DEBUG=True

echo [1/3] 환경 변수 설정 중...
echo - PRODUCTION=False
echo - FLASK_ENV=development
echo - FLASK_DEBUG=True
echo.

REM 백엔드 시작 (새 창)
echo [2/3] 백엔드 시작 중...
start "Monitoring Backend" cmd /k "cd backend && python app.py"
echo ✅ 백엔드 시작됨 (새 창)
echo.

REM 프론트엔드 시작 (새 창)
echo [3/3] 프론트엔드 시작 중...
timeout /t 2 /nobreak
start "Monitoring Frontend" cmd /k "cd frontend && npm run dev"
echo ✅ 프론트엔드 시작됨 (새 창)
echo.

echo ========================================
echo  개발 서버 시작됨
echo ========================================
echo.
echo 📍 프론트엔드: http://localhost:5173
echo 📍 백엔드: http://localhost:8080
echo.
echo 두 개의 새 창이 열렸습니다:
echo 1. Backend 창: Flask 개발 서버
echo 2. Frontend 창: Vite 개발 서버
echo.
echo 종료하려면 각 창에서 Ctrl + C 입력
echo.
echo ========================================
echo.

pause
