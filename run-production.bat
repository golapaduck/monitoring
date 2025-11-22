@echo off
chcp 65001 > nul
echo ========================================
echo   Monitoring 프로젝트 (프로덕션 모드)
echo ========================================
echo.

:: 빌드 파일 확인
if not exist "frontend\dist\index.html" (
    echo ❌ 프론트엔드 빌드 파일이 없습니다.
    echo.
    echo 먼저 빌드를 실행하세요:
    echo   build.bat
    echo.
    pause
    exit /b 1
)

:: 환경 변수 설정
set PRODUCTION=True

:: 서버 정보 출력
echo ✅ 프로덕션 모드로 실행합니다
echo.
echo 📦 백엔드 + 프론트엔드 통합 서버
echo 🌐 URL: http://localhost:8080
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요
echo ========================================
echo.

:: Python 서버 실행
cd backend
python -u app.py
