@echo off
chcp 65001 > nul
echo ========================================
echo   Monitoring 프로젝트 배포
echo ========================================
echo.

:: 1단계: 프론트엔드 빌드
echo [1/2] 프론트엔드 빌드 중...
cd frontend
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 프론트엔드 빌드 실패
    cd ..
    pause
    exit /b 1
)
cd ..
echo ✅ 프론트엔드 빌드 완료
echo.

:: 2단계: .env 파일 백업 및 프로덕션 모드 설정
echo [2/2] 프로덕션 모드 설정 중...
if exist ".env" (
    if not exist ".env.backup" (
        copy ".env" ".env.backup" > nul
    )
)

:: .env 파일에서 PRODUCTION=False를 PRODUCTION=True로 변경
powershell -Command "(Get-Content .env) -replace 'PRODUCTION=False', 'PRODUCTION=True' | Set-Content .env"
echo ✅ 프로덕션 모드 활성화
echo.

:: 배포 완료 메시지
echo ========================================
echo   배포 완료!
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
