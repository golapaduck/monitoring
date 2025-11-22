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

:: .env 파일 백업 및 프로덕션 모드 설정
echo [설정] .env 파일 업데이트 중...
if exist ".env" (
    if not exist ".env.backup" (
        copy ".env" ".env.backup" > nul
    )
)

:: .env 파일에서 PRODUCTION=False를 PRODUCTION=True로 변경
powershell -Command "(Get-Content .env) -replace 'PRODUCTION=False', 'PRODUCTION=True' | Set-Content .env"
echo ✅ 프로덕션 모드 활성화
echo.

:: 서버 정보 출력
echo ========================================
echo   프로덕션 모드로 실행합니다
echo ========================================
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

:: 서버 종료 후 .env 복원
cd ..
echo.
echo [정리] .env 파일 복원 중...
if exist ".env.backup" (
    copy ".env.backup" ".env" > nul
    del ".env.backup"
    echo ✅ .env 파일 복원 완료
)
