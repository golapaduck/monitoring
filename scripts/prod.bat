@echo off
REM ============================================
REM 프로덕션 모드 실행 스크립트
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Monitoring System - Production Mode
echo ========================================
echo.

REM 프로젝트 루트 디렉토리로 이동
cd /d "%~dp0.."

REM 환경 변수 설정
set PRODUCTION=True
set FLASK_ENV=production

echo [1/3] 환경 변수 설정 중...
echo - PRODUCTION=True
echo - FLASK_ENV=production
echo.

REM 프론트엔드 빌드 확인
echo [2/3] 프론트엔드 빌드 확인 중...
if not exist "frontend\dist" (
    echo ⚠️  프론트엔드 빌드 파일이 없습니다!
    echo 빌드 중...
    cd frontend
    call npm run build
    if errorlevel 1 (
        echo ❌ 프론트엔드 빌드 실패!
        pause
        exit /b 1
    )
    cd ..
    echo ✅ 프론트엔드 빌드 완료
) else (
    echo ✅ 프론트엔드 빌드 파일 확인됨
)
echo.

REM 백엔드 실행
echo [3/3] 백엔드 시작 중...
echo.
echo ========================================
echo  서버 시작됨
echo ========================================
echo.
echo 📍 접속 주소: http://localhost:8080
echo 📊 시스템 리소스: http://localhost:8080/api/system/stats
echo 📋 프로그램 목록: http://localhost:8080/api/programs
echo.
echo 종료하려면: Ctrl + C
echo.
echo ========================================
echo.

python serve.py

echo.
echo ========================================
echo  서버 종료됨
echo ========================================
echo.

pause
